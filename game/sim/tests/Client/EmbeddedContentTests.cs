using NUnit.Framework;
using SharpWR.Client;
using SharpWR.Unity;

namespace SharpWR.Sim.Tests.Client
{
    /// <summary>The Unity build loads content from generated C# constants; they must stay loadable.</summary>
    public class EmbeddedContentTests
    {
        [Test]
        public void UnityEmbeddedContentBuildsThePracticeArena()
        {
            PracticeGame g = PracticeGame.Create(EmbeddedReferenceContent.SamiraJson, EmbeddedContent.DuelBotProfilesJson, 9, "medium", 1);
            Assert.That(g.Session.Match.UnitCount, Is.EqualTo(3));
            Assert.That(g.Champion.Shippable, Is.False, "reference content stays non-shippable");
            for (int t = 0; t < 300; t++) g.Session.Step();
        }
    }
}
