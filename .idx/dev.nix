# To learn more about how to use Nix to configure your environment
# see: https://developers.google.com/idx/guides/customize-idx-env
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-23.11"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.terraform
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.virtualenv
  ];

  # Sets environment variables in the workspace
  env = {
    GOOGLE_PROJECT = "novo-calendar";
    CLOUDSDK_CORE_PROJECT = "novo-calendar";
    TF_VAR_project = "novo-calendar";
    # Quieter Terraform logs
    TF_IN_AUTOMATION = "true";
  };

  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      "hashicorp.terraform"
      "ms-python.python"
    ];

    # Enable previews
    previews = {
      enable = true;
      previews = {
        web = {
          command = [
            "streamlit"
            "run"
            "src/app.py"
            "--server.port"
            "$PORT"
          ];

          manager = "web";
        };
      };
    };

    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        default.openFiles = [
          "README.md"
          "src/services/task_service.py"
        ];
        terraform = ''
          terraform init --upgrade
          terraform apply -parallelism=20 --auto-approve -compact-warnings
        '';
        python = ''
          python -m pip install -r requirements.txt
        '';
      };
      # Runs when the workspace is (re)started
      onStart = {
         terraform = ''
          terraform apply -parallelism=20 --auto-approve -compact-warnings
        '';
      };
    };
  };
} 