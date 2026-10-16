using UnityEngine;

namespace SharpWR.Unity
{
    /// <summary>
    /// Starts the practice arena in whatever scene loads first, so no scene file has to be
    /// authored by hand. Remove this (or add a SharpWRGame yourself) once real scenes exist.
    /// </summary>
    public static class Bootstrap
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Start()
        {
            if (Object.FindAnyObjectByType<SharpWRGame>() == null)
                new GameObject("SharpWR").AddComponent<SharpWRGame>();
        }
    }
}
