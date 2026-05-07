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
    overlays.default = final: _prev: rec {
      simyan = final.callPackage ({python3Packages, ...}: let
        pname = "simyan";
        tag = head (
          match ".*__version__ = \"([^\"]+)\".*"
          (readFile "${simyan-src}/${pname}/__init__.py")
        );
      in
        python3Packages.buildPythonPackage {
          inherit pname;
          src = simyan-src;
          version = "${tag}+${substring 0 7 simyan-src.rev}";
          format = "pyproject";

          build-system = with python3Packages; [hatchling];
          dependencies = with python3Packages; [
            httpx
            ((pydantic.override (o: {
                pydantic-core = o.pydantic-core.overridePythonAttrs rec {
                  version = "2.46.0";
                  src = final.fetchPypi {
                    pname = "pydantic_core";
                    inherit version;
                    hash = "sha256-gtJJjJa+R7R+kD4TeNHQ93AJfsVuqVMyLzmTanzzSXc=";
                  };

                  cargoDeps = final.rustPlatform.fetchCargoVendor {
                    inherit pname version src;
                    hash = "sha256-jh3omP+gMI3QxISa0AdDq9R7U0Q1m9Ya2mWdJAIVqvs=";
                  };
                };
              })).overridePythonAttrs rec {
                version = "2.13.0";
                src = final.fetchPypi {
                  pname = "pydantic";
                  inherit version;
                  hash = "sha256-uJtXW25nDr9udEjAG0GyRPRx7dJ2zQtv4C5+esoyAHA=";
                };
              })
            pyrate-limiter
            requests
          ];

          pythonImportChecks = [pname];
        }) {};

      libgencomics = final.callPackage ({python3Packages, ...}: let
        pname = "libgencomics";
        tag = (fromTOML (readFile ./pyproject.toml)).project.version;
      in
        python3Packages.buildPythonPackage {
          inherit pname;
          version = "${tag}+${self.shortRev or "dirty"}";
          format = "pyproject";
          src = ./.;

          build-system = with python3Packages; [setuptools];
          dependencies = with python3Packages; [
            aiohttp
            beautifulsoup4
            requests
            simyan
          ];

          pythonImportChecks = [pname];
        }) {};
    };

    packages = perSystem (pkgs: {
      inherit (pkgs) libgencomics;

      default = pkgs.libgencomics;
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
