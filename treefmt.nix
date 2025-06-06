{
  lib,
  pkgs,
  ...
}: {
  projectRootFile = "flake.lock";

  settings.formatter = {
    "basedpyright" = {
      command = lib.getExe pkgs.basedpyright;
      includes = ["*.py"];
    };
  };

  programs.ruff.format = true;
  programs.ruff.check = true;

  programs.toml-sort.enable = true;
  programs.yamlfmt.enable = true;

  programs.alejandra.enable = true;
  programs.deadnix.enable = true;
}
