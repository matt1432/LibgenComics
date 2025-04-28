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
          libgen-api-comicvine = pyFinal.callPackage ({
            # nix build inputs
            buildPythonPackage,
            # python deps
            beautifulsoup4,
            requests,
            ...
          }: let
            pname = "libgen-api-comicvine";
            version = let
              matchVersion = builtins.match ".*version=[\"']([^\"']+)[\"'].*";
            in
              builtins.head (matchVersion (builtins.readFile ./setup.py));
          in
            buildPythonPackage {
              inherit pname version;
              format = "setuptools";
              src = ./.;
              dependencies = [
                beautifulsoup4
                requests
              ];
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
          (python3Packages.python.withPackages (ps: with python3Packages; [
            beautifulsoup4
            libgen-api-comicvine
            pytest
            requests
          ]))
        ];
      };
    });
  };
}
