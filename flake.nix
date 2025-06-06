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
    treefmt-nix,
    ...
  }: let
    inherit (builtins) fromTOML readFile substring;

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
            fetchFromGitHub,
            # python deps
            eval-type-backport,
            hatchling,
            pydantic,
            ratelimit,
            requests,
            ...
          }: let
            pname = "simyan";
            rev = "92050acb36eace59419a98a86f74c87f55f53034";
            src = fetchFromGitHub {
              owner = "Metron-Project";
              repo = "Simyan";
              inherit rev;
              hash = "sha256-DfbjfxSMlxYo4qDJMJ9btr09iU9wHSV8QYRiptsxlXQ=";
            };
          in
            buildPythonPackage {
              inherit pname src;
              version = "1.4.0+${substring 0 7 rev}";
              format = "pyproject";

              build-system = [hatchling];
              dependencies = [
                eval-type-backport
                pydantic
                ratelimit
                requests
              ];

              pythonImportChecks = [pname];
            }) {};

          libgencomics = pyFinal.callPackage ({
            # nix build inputs
            buildPythonPackage,
            # python deps
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
