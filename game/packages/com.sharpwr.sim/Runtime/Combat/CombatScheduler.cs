using System;
using System.Collections.Generic;
using SharpWR.Sim.Core;

namespace SharpWR.Sim.Combat
{
    /// <summary>A pending action. Plain data: no delegates, so the queue is serializable for rollback.</summary>
    public readonly struct ScheduledEvent
    {
        public readonly SimTime Time;
        public readonly EventPhase Phase;
        public readonly long Sequence;
        public readonly CombatEventKind Kind;
        public readonly int Source;
        public readonly int Target;
        public readonly int ActionId;

        public ScheduledEvent(SimTime time, EventPhase phase, long sequence, CombatEventKind kind,
                              int source, int target, int actionId)
        {
            Time = time; Phase = phase; Sequence = sequence; Kind = kind;
            Source = source; Target = target; ActionId = actionId;
        }

        /// <summary>Total order: time, then phase, then insertion sequence. Never ties.</summary>
        public static int Compare(in ScheduledEvent a, in ScheduledEvent b)
        {
            int c = a.Time.Micros.CompareTo(b.Time.Micros);
            if (c != 0) return c;
            c = ((byte)a.Phase).CompareTo((byte)b.Phase);
            return c != 0 ? c : a.Sequence.CompareTo(b.Sequence);
        }
    }

    /// <summary>
    /// Binary min-heap of scheduled events. The fixed-step loop calls
    /// <see cref="TryPopDue"/> until nothing is due at or before the end of the current tick.
    /// Events scheduled while draining (e.g. an impact scheduling damage at the same
    /// microsecond) are honoured in the same drain because ordering is re-evaluated each pop.
    /// </summary>
    public sealed class CombatScheduler
    {
        private readonly List<ScheduledEvent> _heap = new List<ScheduledEvent>(128);
        private long _nextSequence;

        public int Count => _heap.Count;

        /// <summary>Exact copy (pending events and sequence counter) for match snapshots.</summary>
        public CombatScheduler Clone()
        {
            var copy = new CombatScheduler { _nextSequence = _nextSequence };
            copy._heap.AddRange(_heap);
            return copy;
        }

        public long Schedule(SimTime time, EventPhase phase, CombatEventKind kind, int source, int target, int actionId)
        {
            long seq = _nextSequence++;
            _heap.Add(new ScheduledEvent(time, phase, seq, kind, source, target, actionId));
            SiftUp(_heap.Count - 1);
            return seq;
        }

        public bool TryPopDue(SimTime inclusiveEnd, out ScheduledEvent next)
        {
            if (_heap.Count == 0 || _heap[0].Time > inclusiveEnd)
            {
                next = default;
                return false;
            }
            next = _heap[0];
            int last = _heap.Count - 1;
            _heap[0] = _heap[last];
            _heap.RemoveAt(last);
            if (_heap.Count > 0) SiftDown(0);
            return true;
        }

        private void SiftUp(int i)
        {
            while (i > 0)
            {
                int parent = (i - 1) / 2;
                if (ScheduledEvent.Compare(_heap[i], _heap[parent]) >= 0) return;
                Swap(i, parent);
                i = parent;
            }
        }

        private void SiftDown(int i)
        {
            int n = _heap.Count;
            while (true)
            {
                int l = 2 * i + 1, r = l + 1, smallest = i;
                if (l < n && ScheduledEvent.Compare(_heap[l], _heap[smallest]) < 0) smallest = l;
                if (r < n && ScheduledEvent.Compare(_heap[r], _heap[smallest]) < 0) smallest = r;
                if (smallest == i) return;
                Swap(i, smallest);
                i = smallest;
            }
        }

        private void Swap(int a, int b)
        {
            ScheduledEvent t = _heap[a];
            _heap[a] = _heap[b];
            _heap[b] = t;
        }
    }
}
