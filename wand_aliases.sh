# wand_aliases.sh

SERVICE_NAME="wand_demo"
APPLICATION_NAME="wand_demo"
USER_DIR="/home/CDTR"
CDTR_DIR="$USER_DIR/CDTR"

alias cdtr="cd $CDTR_DIR"
alias wand-appsettings="nano $USER_DIR/CDTR/Current/appsettings.yml"
alias wand-environment="nano $USER_DIR/CDTR/Current/appsettings.env.yml"
alias wand-install="bash $CDTR_DIR/install.sh"
alias wand-start="sudo systemctl start $SERVICE_NAME"
alias wand-stop="sudo systemctl stop $SERVICE_NAME"
alias wand-restart="sudo systemctl restart $SERVICE_NAME"
alias wand-status="sudo systemctl status $SERVICE_NAME"
alias wand-enable="sudo systemctl enable $SERVICE_NAME"
alias wand-disable="sudo systemctl disable $SERVICE_NAME"
alias wand-debug="$USER_DIR/CDTR/Current/$APPLICATION_NAME"
