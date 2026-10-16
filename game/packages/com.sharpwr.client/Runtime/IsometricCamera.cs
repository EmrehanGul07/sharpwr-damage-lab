using System;

namespace SharpWR.Client
{
    /// <summary>
    /// Fixed-angle follow camera math (no engine types). Game units map to engine metres by
    /// <see cref="MetresPerUnit"/>; the Unity layer applies the resulting pose.
    /// </summary>
    public sealed class IsometricCamera
    {
        public const double MetresPerUnit = 0.01;    // 100 game units = 1 m (attack range 525 = 5.25 m)

        public double PitchDegrees = 55;
        public double YawDegrees = 0;
        public double Distance = 16;                  // metres from the focus point
        public double FollowSharpness = 10;           // 1/s, exponential smoothing

        public double FocusX, FocusZ;                 // metres

        public void Snap(double unitX, double unitZ) { FocusX = unitX * MetresPerUnit; FocusZ = unitZ * MetresPerUnit; }

        public void Follow(double unitX, double unitZ, double frameSeconds)
        {
            double t = 1 - Math.Exp(-FollowSharpness * Math.Max(0, frameSeconds));
            FocusX += (unitX * MetresPerUnit - FocusX) * t;
            FocusZ += (unitZ * MetresPerUnit - FocusZ) * t;
        }

        /// <summary>Camera position in metres (x, y, z); it looks at (FocusX, 0, FocusZ).</summary>
        public (double X, double Y, double Z) Position()
        {
            double pitch = PitchDegrees * Math.PI / 180, yaw = YawDegrees * Math.PI / 180;
            double horizontal = Distance * Math.Cos(pitch);
            return (FocusX - Math.Sin(yaw) * horizontal, Distance * Math.Sin(pitch), FocusZ - Math.Cos(yaw) * horizontal);
        }

        /// <summary>Screen joystick (right, up) → world direction (dx, dz) for this camera yaw.</summary>
        public (double Dx, double Dz) ScreenToWorldDirection(double right, double up)
        {
            double yaw = YawDegrees * Math.PI / 180;
            return (right * Math.Cos(yaw) + up * Math.Sin(yaw), -right * Math.Sin(yaw) + up * Math.Cos(yaw));
        }
    }
}
