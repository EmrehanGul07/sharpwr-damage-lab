// Minimal signatures of the Unity APIs used by com.sharpwr.unity, so CI can catch plain C#
// errors without a Unity licence. NOT a substitute for compiling in the Unity editor:
// it cannot detect a wrong Unity signature, only mistakes in our own code.
#pragma warning disable CS0067, CS0649, CS0626, CS0169, CS0414
namespace UnityEngine
{
    public class Object
    {
        public string name;
        public static T FindAnyObjectByType<T>() where T : Object => null;
        public static void Destroy(Object o) { }
        public static implicit operator bool(Object o) => o != null;
    }
    public class Component : Object { public GameObject gameObject; public Transform transform; public T GetComponent<T>() => default; }
    public class Behaviour : Component { }
    public class MonoBehaviour : Behaviour { }
    public sealed class GameObject : Object
    {
        public GameObject(string name) { }
        public string tag;
        public Transform transform;
        public T AddComponent<T>() where T : Component, new() => new T();
        public T GetComponent<T>() => default;
        public void SetActive(bool value) { }
        public static GameObject CreatePrimitive(PrimitiveType type) => new GameObject("");
    }
    public enum PrimitiveType { Sphere, Capsule, Cylinder, Cube, Plane, Quad }
    public class Transform : Component
    {
        public Vector3 position; public Quaternion rotation; public Vector3 localScale;
        public void LookAt(Vector3 p) { }
    }
    public class Collider : Component { }
    public class Renderer : Component { public Material material; }
    public class Material { public Color color; }
    public enum CameraClearFlags { Skybox = 1, SolidColor = 2 }
    public sealed class Camera : Behaviour
    {
        public static Camera main;
        public CameraClearFlags clearFlags; public Color backgroundColor;
        public Ray ScreenPointToRay(Vector3 p) => default;
        public Vector3 WorldToScreenPoint(Vector3 p) => default;
    }
    public enum LightType { Spot, Directional, Point }
    public sealed class Light : Behaviour { public LightType type; }
    public struct Ray { public Vector3 origin; public Vector3 direction; }
    public struct Vector2
    {
        public float x, y;
        public Vector2(float x, float y) { this.x = x; this.y = y; }
        public float magnitude => 0; public float sqrMagnitude => 0;
        public void Normalize() { }
        public static Vector2 ClampMagnitude(Vector2 v, float m) => v;
        public static Vector2 operator +(Vector2 a, Vector2 b) => a;
        public static Vector2 operator -(Vector2 a, Vector2 b) => a;
        public static Vector2 operator /(Vector2 a, float d) => a;
        public static implicit operator Vector3(Vector2 v) => default;
        public static implicit operator Vector2(Vector3 v) => default;
    }
    public struct Vector3
    {
        public float x, y, z;
        public Vector3(float x, float y, float z) { this.x = x; this.y = y; this.z = z; }
        public static Vector3 up => default;
        public float sqrMagnitude => 0;
        public static Vector3 operator +(Vector3 a, Vector3 b) => a;
        public static Vector3 operator -(Vector3 a, Vector3 b) => a;
        public static Vector3 operator *(Vector3 a, float d) => a;
    }
    public struct Quaternion
    {
        public static Quaternion Euler(float x, float y, float z) => default;
        public static Quaternion LookRotation(Vector3 forward) => default;
    }
    public struct Color
    {
        public Color(float r, float g, float b) { } public Color(float r, float g, float b, float a) { }
        public static Color white => default; public static Color gray => default;
    }
    public struct Rect
    {
        public Rect(float x, float y, float w, float h) { this.x = x; this.y = y; width = w; height = h; }
        public float x, y, width, height;
    }
    public struct Matrix4x4 { }
    public static class Mathf
    {
        public const float Rad2Deg = 57.29578f;
        public static float Abs(float f) => f; public static float Atan2(float y, float x) => 0;
        public static int RoundToInt(float f) => 0;
    }
    public static class Screen { public static int width, height; }
    public static class Application { public static int targetFrameRate; }
    public static class Time { public static float deltaTime; }
    public enum RuntimeInitializeLoadType { AfterSceneLoad, BeforeSceneLoad }
    [System.AttributeUsage(System.AttributeTargets.Method)]
    public sealed class RuntimeInitializeOnLoadMethodAttribute : System.Attribute
    {
        public RuntimeInitializeOnLoadMethodAttribute(RuntimeInitializeLoadType t) { }
    }
    public class Texture { }
    public sealed class Texture2D : Texture { public static Texture2D whiteTexture; }
    public enum ScaleMode { StretchToFill, ScaleAndCrop, ScaleToFit }
    public enum TextAnchor { UpperLeft, MiddleCenter }
    public sealed class GUIStyle
    {
        public GUIStyle(GUIStyle other) { }
        public int fontSize; public TextAnchor alignment;
    }
    public sealed class GUISkin { public GUIStyle label, button; }
    public static class GUI
    {
        public static Color color; public static Matrix4x4 matrix; public static GUISkin skin;
        public static void Label(Rect r, string text, GUIStyle style) { }
        public static bool Button(Rect r, string text, GUIStyle style) => false;
        public static void DrawTexture(Rect r, Texture t) { }
        public static void DrawTexture(Rect r, Texture t, ScaleMode m, bool alphaBlend, float aspect, Color color, float borderWidth, float borderRadius) { }
    }
    public static class GUIUtility { public static void RotateAroundPivot(float angle, Vector2 pivot) { } }
    public enum TouchPhase { Began, Moved, Stationary, Ended, Canceled }
    public struct Touch { public int fingerId; public Vector2 position; public TouchPhase phase; }
    public enum KeyCode { Q, W, E, R, A, S, F1 }
    public static class Input
    {
        public static bool simulateMouseWithTouches; public static int touchCount; public static Vector3 mousePosition;
        public static Touch GetTouch(int i) => default;
        public static bool GetMouseButtonDown(int b) => false; public static bool GetMouseButtonUp(int b) => false;
        public static bool GetMouseButton(int b) => false; public static bool GetKeyDown(KeyCode k) => false;
    }
}
namespace UnityEngine.InputSystem.Controls
{
    public class ButtonControl { public bool wasPressedThisFrame, wasReleasedThisFrame, isPressed; }
    public sealed class IntegerControl { public int ReadValue() => 0; }
    public sealed class Vector2Control { public UnityEngine.Vector2 ReadValue() => default; }
    public sealed class TouchControl { public ButtonControl press; public IntegerControl touchId; public Vector2Control position; }
}
namespace UnityEngine.InputSystem
{
    using UnityEngine.InputSystem.Controls;
    public sealed class Touchscreen { public static Touchscreen current; public TouchControl[] touches; }
    public sealed class Mouse { public static Mouse current; public Vector2Control position; public ButtonControl leftButton, rightButton; }
    public sealed class KeyControl : ButtonControl { }
    public sealed class Keyboard
    {
        public static Keyboard current;
        public KeyControl qKey, wKey, eKey, rKey, aKey, sKey, f1Key;
    }
}
