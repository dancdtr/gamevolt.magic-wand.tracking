# wand_aliases.sh

APPLICATION_NAME="wand_demo"

USER_DIR="$HOME"
CDTR_DIR="$USER_DIR/CDTR"
CURRENT_DIR="$CDTR_DIR/Current"

alias cdtr="cd $CDTR_DIR"

alias wand-aliases="nano ~/.wand_aliases.sh"
alias wand-appsettings="nano $USER_DIR/CDTR/Current/_internal/appsettings.yml"
alias wand-environment="nano $USER_DIR/CDTR/Current/appsettings.env.yml"
alias wand-install="bash $CDTR_DIR/install.sh"
alias wand-start="$CURRENT_DIR/$APPLICATION_NAME"
 
alias source-bash="source ~/.bashrc"

wand-builds() {
  local dir="$CDTR_DIR"
  local app="$APPLICATION_NAME"

  shopt -s nullglob
  local files=( "$dir/${app}-"*.zip )
  shopt -u nullglob

  if (( ${#files[@]} == 0 )); then
    echo "No build artefacts found matching: $dir/${app}-*.zip"
    return 0
  fi

  ls -lh -t -- "${files[@]}"
}

# wand_aliases.sh
wand-start # launch the app

wand-appsettings # open appsettings.yml - do not edit!
wand-environment # open appsettings.env.yml for editing

wand-install # <version> install target build
wand-builds # list available app builds

cdtr # change directory to CDTR

wand-aliases # open ~/.wand_aliases.sh file for editing
source-bash #shortcut to resource .bashrc - must do after editing ~/.wand_aliases.sh
