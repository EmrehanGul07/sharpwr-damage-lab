using SharpWR.Sim.Numerics;

namespace SharpWR.Sim.Contracts
{
    public enum Team : byte { Neutral = 0, Blue = 1, Red = 2 }

    /// <summary>Why a command was refused (logged as the Rejected event's ActionId).</summary>
    public enum RejectReason : byte
    {
        UnknownUnit = 1,
        CannotAct = 2,
        InvalidTarget = 3,
        UnsupportedCommand = 4,
        OnCooldown = 5,
        NotEnoughResource = 6,
        Locked = 7,
        OutOfRange = 8,
        UnsupportedMechanic = 9,
    }

    public enum CommandKind : byte
    {
        None = 0,
        Move = 1,        // walk to Point
        Stop = 2,        // clear orders
        AttackUnit = 3,  // chase and attack TargetUnit
        Cast = 10,       // ability Slot at Point / TargetUnit (M1 ability framework)
    }

    /// <summary>
    /// Player or bot intent for one unit. The only way anything outside the simulation can
    /// influence it (offline, AI and network all produce these).
    /// </summary>
    public readonly struct Command
    {
        public readonly int Unit;
        public readonly CommandKind Kind;
        public readonly int TargetUnit;
        public readonly FixVec2 Point;
        public readonly byte Slot;

        public Command(int unit, CommandKind kind, int targetUnit, FixVec2 point, byte slot = 0)
        {
            Unit = unit; Kind = kind; TargetUnit = targetUnit; Point = point; Slot = slot;
        }

        public static Command MoveTo(int unit, FixVec2 point) => new Command(unit, CommandKind.Move, 0, point);
        public static Command Attack(int unit, int target) => new Command(unit, CommandKind.AttackUnit, target, FixVec2.Zero);
        public static Command StopUnit(int unit) => new Command(unit, CommandKind.Stop, 0, FixVec2.Zero);
    }
}
