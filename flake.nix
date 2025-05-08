{
  inputs = {
    nixpkgs = {
      type = "github";
      owner = "NixOS";
      repo = "nixpkgs";
      ref = "nixos-unstable";
    };

    pycomicvine = {
      type = "github";
      owner = "matt1432";
      repo = "pycomicvine";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        systems.follows = "systems";
        treefmt-nix.follows = "treefmt-nix";
      };
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
  };

  outputs = {
    self,
    systems,
    nixpkgs,
    pycomicvine,
    treefmt-nix,
    ...
  }: let
    inherit (builtins) fromTOML readFile;

    perSystem = attrs:
      nixpkgs.lib.genAttrs (import systems) (system:
        attrs (import nixpkgs {
          inherit system;
          overlays = [
            pycomicvine.overlays.default
            self.overlays.default
          ];
        }));
  in {
    overlays.default = _final: prev: {
      python3Packages = prev.python3Packages.override {
        overrides = pyFinal: _pyPrev: {
          inherit (prev.python3Packages) pycomicvine;

          libgencomics = pyFinal.callPackage ({
            # nix build inputs
            buildPythonPackage,
            # python deps
            beautifulsoup4,
            pycomicvine,
            requests,
            setuptools,
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
                beautifulsoup4
                pycomicvine
                requests
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
          alejandra

          (python3Packages.python.withPackages (_ps:
            with python3Packages; [
              beautifulsoup4
              libgencomics
              pycomicvine
              requests
            ]))
        ];
      };
    });
  };
}
