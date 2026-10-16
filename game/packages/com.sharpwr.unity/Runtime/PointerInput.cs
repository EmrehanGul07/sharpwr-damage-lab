using System.Collections.Generic;
using UnityEngine;
#if SHARPWR_INPUT_SYSTEM && ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.Controls;
#endif

namespace SharpWR.Unity
{
    public enum PointerPhase { Began, Held, Ended }

    /// <summary>One finger, or the left mouse button (Id = -1). Positions are pixels, bottom-left origin.</summary>
    public struct Pointer
    {
        public int Id;
        public Vector2 Position;
        public PointerPhase Phase;
    }

    /// <summary>
    /// Reads touches, mouse and keyboard through the Input System package when it is installed
    /// and active, otherwise through the legacy Input Manager. Same output either way.
    /// </summary>
    public sealed class PointerInput
    {
        public readonly List<Pointer> Pointers = new List<Pointer>(8);
        public Vector2 MousePosition;
        public bool RightClick, KeyQ, KeyW, KeyE, KeyR, KeyA, KeyS, ToggleDebug;

        public void Poll()
        {
            Pointers.Clear();
            RightClick = KeyQ = KeyW = KeyE = KeyR = KeyA = KeyS = ToggleDebug = false;
#if SHARPWR_INPUT_SYSTEM && ENABLE_INPUT_SYSTEM
            if (Touchscreen.current != null)
            {
                foreach (TouchControl t in Touchscreen.current.touches)
                {
                    PointerPhase? phase = t.press.wasPressedThisFrame ? PointerPhase.Began
                        : t.press.wasReleasedThisFrame ? PointerPhase.Ended
                        : t.press.isPressed ? PointerPhase.Held : (PointerPhase?)null;
                    if (phase.HasValue)
                        Pointers.Add(new Pointer { Id = t.touchId.ReadValue(), Position = t.position.ReadValue(), Phase = phase.Value });
                }
            }
            Mouse mouse = Mouse.current;
            if (mouse != null)
            {
                MousePosition = mouse.position.ReadValue();
                PointerPhase? phase = mouse.leftButton.wasPressedThisFrame ? PointerPhase.Began
                    : mouse.leftButton.wasReleasedThisFrame ? PointerPhase.Ended
                    : mouse.leftButton.isPressed ? PointerPhase.Held : (PointerPhase?)null;
                if (phase.HasValue) Pointers.Add(new Pointer { Id = -1, Position = MousePosition, Phase = phase.Value });
                RightClick = mouse.rightButton.wasPressedThisFrame;
            }
            Keyboard k = Keyboard.current;
            if (k != null)
            {
                KeyQ = k.qKey.wasPressedThisFrame; KeyW = k.wKey.wasPressedThisFrame;
                KeyE = k.eKey.wasPressedThisFrame; KeyR = k.rKey.wasPressedThisFrame;
                KeyA = k.aKey.wasPressedThisFrame; KeyS = k.sKey.wasPressedThisFrame;
                ToggleDebug = k.f1Key.wasPressedThisFrame;
            }
#elif ENABLE_LEGACY_INPUT_MANAGER
            Input.simulateMouseWithTouches = false;
            for (int i = 0; i < Input.touchCount; i++)
            {
                Touch t = Input.GetTouch(i);
                PointerPhase phase = t.phase == TouchPhase.Began ? PointerPhase.Began
                    : t.phase == TouchPhase.Ended || t.phase == TouchPhase.Canceled ? PointerPhase.Ended
                    : PointerPhase.Held;
                Pointers.Add(new Pointer { Id = t.fingerId, Position = t.position, Phase = phase });
            }
            MousePosition = Input.mousePosition;
            if (Input.touchCount == 0)
            {
                if (Input.GetMouseButtonDown(0)) Pointers.Add(new Pointer { Id = -1, Position = MousePosition, Phase = PointerPhase.Began });
                else if (Input.GetMouseButtonUp(0)) Pointers.Add(new Pointer { Id = -1, Position = MousePosition, Phase = PointerPhase.Ended });
                else if (Input.GetMouseButton(0)) Pointers.Add(new Pointer { Id = -1, Position = MousePosition, Phase = PointerPhase.Held });
                RightClick = Input.GetMouseButtonDown(1);
            }
            KeyQ = Input.GetKeyDown(KeyCode.Q); KeyW = Input.GetKeyDown(KeyCode.W);
            KeyE = Input.GetKeyDown(KeyCode.E); KeyR = Input.GetKeyDown(KeyCode.R);
            KeyA = Input.GetKeyDown(KeyCode.A); KeyS = Input.GetKeyDown(KeyCode.S);
            ToggleDebug = Input.GetKeyDown(KeyCode.F1);
#endif
        }
    }
}
