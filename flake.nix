{
  inputs = {
    nixpkgs = {
      type = "github";
      owner = "NixOS";
      repo = "nixpkgs";
      ref = "nixos-unstable";
    };

    systems = {
      type = "github";
      owner = "nix-systems";
      repo = "default-linux";
    };
  };

  outputs = {
    self,
    systems,
    nixpkgs,
    ...
  }: let
    perSystem = attrs:
      nixpkgs.lib.genAttrs (import systems) (system:
        attrs (import nixpkgs {
          inherit system;
          overlays = [
            self.overlays.default
          ];
        }));
  in {
    overlays.default = final: prev: {
      python3Packages = prev.python3Packages.override {
        overrides = pyFinal: pyPrev: {
          pycomicvine = pyFinal.callPackage ({
            # nix build inputs
            buildPythonPackage,
            fetchFromGitHub,
            # python deps
            simplejson,
            python-dateutil,
            ...
          }:
            buildPythonPackage {
              pname = "pycomicvine";
              version = "1.0.0";

              format = "setuptools";

              src = fetchFromGitHub {
                owner = "miri64";
                repo = "pycomicvine";
                rev = "bfc72ceb585c7d63bd5c603a51e838f81ce2d348";
                hash = "sha256-vfqfcR4qFK9exLv727ppEJLEpwwGMd/xnLuMF6mXeP4=";
              };

              postPatch = ''
                substituteInPlace ./setup.py --replace-fail "**extra" ""
              '';

              dependencies = [simplejson python-dateutil];
            }) {};

          libgen-api-comicvine = pyFinal.callPackage ({
            # nix build inputs
            buildPythonPackage,
            # python deps
            beautifulsoup4,
            pycomicvine,
            requests,
            setuptools,
            ...
          }: let
            pname = "libgen-api-comicvine";
            version = (builtins.fromTOML (builtins.readFile ./pyproject.toml)).project.version;
          in
            buildPythonPackage {
              inherit pname version;
              format = "pyproject";
              src = ./.;
              build-system = [setuptools];
              dependencies = [
                beautifulsoup4
                pycomicvine
                requests
              ];
              pythonImportChecks = ["libgen_api_comicvine"];
            }) {};
        };
      };
    };

    packages = perSystem (pkgs: {
      inherit (pkgs.python3Packages) libgen-api-comicvine;

      default = pkgs.python3Packages.libgen-api-comicvine;
    });

    formatter = perSystem (pkgs: pkgs.alejandra);

    devShells = perSystem (pkgs: {
      default = pkgs.mkShell {
        packages = with pkgs; [
          alejandra

          (python3Packages.python.withPackages (ps:
            with python3Packages; [
              beautifulsoup4
              libgen-api-comicvine
              pycomicvine
              requests
            ]))
        ];
      };
    });
  };
}
