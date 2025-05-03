{pkgs, ...}: {
  projectRootFile = "flake.lock";

  programs.mypy = {
    enable = true;
    directories."" = {
      modules = ["libgencv"];
      extraPythonPackages = with pkgs.python3Packages; (libgencv.dependencies
        ++ [
          libgencv
          types-beautifulsoup4
          types-requests
        ]);
    };
  };

  programs.ruff.format = true;
  programs.ruff.check = true;

  programs.toml-sort.enable = true;
  programs.yamlfmt.enable = true;

  programs.alejandra.enable = true;
  programs.deadnix.enable = true;
}
