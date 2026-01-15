# wand_aliases.sh

APPLICATION_NAME="wand_demo"
USER_DIR="~"
CDTR_DIR="$USER_DIR/CDTR"
CURRENT_DIR="$CDTR_DIR/Current"

alias cdtr="cd $CDTR_DIR"
alias wand-appsettings="nano $USER_DIR/CDTR/Current/appsettings.yml"
alias wand-environment="nano $USER_DIR/CDTR/Current/appsettings.env.yml"
alias wand-install="bash $CDTR_DIR/install.sh"
alias wand-start="$CURRENT_DIR/$APPLICATION_NAME"
