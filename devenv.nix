{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/basics/
  env.GREET = "devenv";

  dotenv.enable = true; # Enable dotenv support


  # https://devenv.sh/packages/
  # Took about 30 mins to build the following setup, quick after that.
  packages = with pkgs; [
    actionlint # GitHub Actions CLI for local testing
    (python311.withPackages (ps:
      with ps; [
        flake8 # Code style checking
        pandas-stubs
        # used by make.py
        typer
        # 📊 Data processing
        pandas # Tabular data manipulation
        numpy # Numerical arrays, math operations

        # 📈 Visualization
        matplotlib # Core plotting
        seaborn # Statistical plots built on matplotlib

        # 🧠 Machine Learning
        scikit-learn # Regression, classification, pipelines, preprocessing
        xgboost # Gradient-boosted trees, performant ML

        # 📦 Experiment Tracking
        mlflow # Model tracking, packaging, metrics/logs
        joblib # Model persistence and parallel computing
        pip


        # 🧪 Testing
        pytest # Unit testing, test discovery
        joblib # Model persistence, parallelism (used by sklearn)
        pyyaml # YAML config parsing
        setuptools # Needed for packaging and version metadata

        # 🧠 Notebooks and Interactive
        ipykernel # Required for Jupyter kernel
        jupyterlab # Web-based notebook interface
        ipython # Rich interactive Python shell

        # ⚡ Serving (optional)
        fastapi # REST API for model serving
        uvicorn # ASGI server for FastAPI apps

      ]))
    jupyter # Optional: CLI for Jupyter
    gum # Optional: CLI tools (e.g., for TUI prompts)
  ];

  # https://devenv.sh/languages/
  # languages.rust.enable = true;

  # https://devenv.sh/processes/
  # processes.cargo-watch.exec = "cargo-watch";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/

  # Define the actionlint pre-commit script
  scripts.actionlint-pre-commit.exec = ''
    echo "Running actionlint pre-commit hook..."
    # Find all GitHub Actions workflow files and lint them with shellcheck integration
    find .github/workflows/ -name "*.y*ml" -print0 | xargs -0 actionlint -color -shellcheck
    if [ $? -ne 0 ]; then
      echo "actionlint found issues. Please fix them before committing."
      exit 1
    fi
    echo "actionlint passed."
  '';

  scripts.hello.exec = ''
    echo hello from $GREET
  '';

  enterShell = ''
    for cmd in "python --version" "git --version" "jupyter kernelspec list "; do
      output=$($cmd)
      gum style --foreground 212 --background 57 --bold "$output"
    done  '';

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };

  # https://devenv.sh/tests/
  enterTest = ''
    echo "Running tests"
    git --version | grep --color=auto "${pkgs.git.version}"
  '';

  # https://devenv.sh/git-hooks/
  git-hooks.hooks = {
    # Enable shellcheck hook (devenv.sh will manage its command)
    shellcheck.enable = true;

  };

   

  # See full reference at https://devenv.sh/reference/options/
}
