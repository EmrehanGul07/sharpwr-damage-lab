Build and test outside Unity:

    dotnet test game/sim/tests/SharpWR.Sim.Tests.csproj

Package versions in the test project are pins chosen at authoring time and have not been
restored in the authoring session (no NuGet access); run `dotnet restore` and update them if needed.
