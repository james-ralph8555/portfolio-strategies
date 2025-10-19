{
  description = "Risk parity portfolio optimization";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonEnv = pkgs.python313.withPackages (ps: with ps; [
          pandas
          yfinance
          numpy
          scipy
          pytest
          pytest-cov
          pytest-mock
          pyyaml
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
          ];
        };

        packages.default = pkgs.writeShellApplication {
          name = "riskparity";
          text = ''
            ${pythonEnv}/bin/python ${./riskparity.py} "$@"
          '';
        };
      });
}