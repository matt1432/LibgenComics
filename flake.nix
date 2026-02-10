{
  inputs = {
    nixpkgs = {
      type = "git";
      url = "https://github.com/NixOS/nixpkgs";
      ref = "nixos-unstable";
      shallow = true;
    };

    systems = {
      type = "github";
      owner = "nix-systems";
      repo = "default-linux";
    };

    treefmt-nix = {
      type = "github";
      owner = "numtide";
      repo = "treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    simyan-src = {
      type = "github";
      owner = "Metron-Project";
      repo = "Simyan";
      flake = false;
    };
  };

  outputs = {
    self,
    systems,
    nixpkgs,
    treefmt-nix,
    simyan-src,
    ...
  }: let
    inherit (builtins) head match readFile substring;

    perSystem = attrs:
      nixpkgs.lib.genAttrs (import systems) (system:
        attrs (import nixpkgs {
          inherit system;
          overlays = [
            self.overlays.default
          ];
        }));
  in {
    overlays.default = _final: prev: {
      python3Packages = prev.python3Packages.override {
        overrides = pyFinal: _pyPrev: {
          simyan = pyFinal.callPackage ({
            # nix build inputs
            buildPythonPackage,
            # python deps
            hatchling,
            pydantic,
            pyrate-limiter,
            requests,
            ...
          }: let
            pname = "simyan";
            tag = head (
              match ".*__version__ = \"([^\"]+)\".*"
              (readFile "${simyan-src}/${pname}/__init__.py")
            );
          in
            buildPythonPackage {
              inherit pname;
              src = simyan-src;
              version = "${tag}+${substring 0 7 simyan-src.rev}";
              format = "pyproject";

              build-system = [hatchling];
              dependencies = [
                pydantic
                pyrate-limiter
                requests
              ];

              pythonImportChecks = [pname];
            }) {};

          libgencomics = pyFinal.callPackage ({
            # nix build inputs
            buildPythonPackage,
            # python deps
            aiohttp,
            beautifulsoup4,
            requests,
            setuptools,
            simyan,
            ...
          }: let
            pname = "libgencomics";
            tag = (fromTOML (readFile ./pyproject.toml)).project.version;
          in
            buildPythonPackage {
              inherit pname;
              version = "${tag}+${self.shortRev or "dirty"}";
              format = "pyproject";
              src = ./.;

              build-system = [setuptools];
              dependencies = [
                aiohttp
                beautifulsoup4
                requests
                simyan
              ];

              pythonImportChecks = [pname];
            }) {};
        };
      };
    };

    packages = perSystem (pkgs: {
      inherit (pkgs.python3Packages) libgencomics;

      default = pkgs.python3Packages.libgencomics;
    });

    formatter = perSystem (pkgs: let
      treefmtEval = treefmt-nix.lib.evalModule pkgs ./treefmt.nix;
    in
      treefmtEval.config.build.wrapper);

    devShells = perSystem (pkgs: {
      default = pkgs.mkShell {
        packages = with pkgs; [
          (python3Packages.python.withPackages (_ps:
            with python3Packages; [
              aiohttp
              beautifulsoup4
              libgencomics
              requests
              simyan
            ]))
        ];
      };
    });
  };
}
