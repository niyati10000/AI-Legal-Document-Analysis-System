{ pkgs }: {
  deps = [
    pkgs.python313
    pkgs.python313Packages.pip
    pkgs.python313Packages.virtualenv
  ];
  env = {
    PYTHONUNBUFFERED = "1";
  };
}
