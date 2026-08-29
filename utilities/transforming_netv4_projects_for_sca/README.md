# Context
To run a supply-chain scan for a dotnet project we must generate the lock file (packages.lock.json) with the command:
`dotnet restore -p:RestorePackagesWithLockFile=True`

However, if the dotnet framework is equal or lower to 4.X then we will see an error like this:
```
Failed to restore ./dotnet_projects/BusinessObjects/BusinessObjects.csproj
```

The message we should expect is:
```
Successfully generated packages.lock.json
```

The reason behind is, the dotnet restore is expecting a `.csproj` file with lines like:
```
<PackageReference Include="Newtonsgot.json" version="13.0.1"/>
```

But it is finding a `.csproj` with lines like this:
```
<Reference Include="Newtonsgot.json" version="13.0.1"/>
```

# Solution
Execute the script:
./transform.sh

Logic:
* Iterate through all the `csproj` files for the current project and execute dotnet utility: `dotnet restore -p:RestorePackagesWithLockFile=True` to generate `package.lock.json` files expected by supply-chain scans.
* If the dotnet restore command fails for all the `csproj` files, then it is likely a .NET project version 4.x, so the logic follows:
* Adding `PackageReference` items for all the `csproj` files (calling the Python script `transform.py`)
* Execute again the dotnet utility: `dotnet restore -p:RestorePackagesWithLockFile=True`
