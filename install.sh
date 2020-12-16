#!/usr/bin/env bash
#
# Download this file and execute it!
# wget https://raw.githubusercontent.com/danielbonhaure/psims/master/install.sh --output-document=install-psims
#

# import gutils.sh
gutils=$(dirname $(readlink -f $0))/gutils.sh
wget --quiet https://raw.githubusercontent.com/danielbonhaure/psims/master/gutils.sh --output-document=${gutils}
source ${gutils}; test $? -ne 0 && exit 1

# print usage help message
usage() {
  echo -e "Usage: install-psims [options] ... \n"
  echo -e "Clone, configure and install pSIMS \n"
  echo -e "Options:"
  echo -e " -f, --dest-folder <arg>       \t Installation folder absolute path. Default: /opt/psims"
  echo -e " -s, --swift-dest-folder <arg> \t Installation folder absolute path for swift. Default: /opt/swift"
  echo -e " -F, --dssat-folder <arg>      \t DSSAT folder absolute path. Default: /opt/dssat"
  echo -e " -X, --dssat-executable <arg>  \t DSSAT executable (in DSSAT folder). Default: dscsm047"
  echo -e " -V, --dssat-version <arg>     \t DSSAT version. Default: 47"
  echo -e " -t, --test-installation       \t Auto-run pSIMS after installation is complete."
  echo -e " -h, --help                    \t Display a help message and quit."
}

# process script inputs
while [[ $# -gt 0 ]]; do
  case $1 in
    -f|--dest-folder) PSIMS_FOLDER=$2; SWIFT_FOLDER=${PSIMS_FOLDER%/*}/swift; shift 2;;
    -s|--swift-dest-folder) SWIFT_FOLDER=$2; shift 2;;
    -F|--dssat-folder) DSSAT_FOLDER=$2; shift 2;;
    -X|--dssat-executable) DSSAT_EXECUTABLE=$2; shift 2;;
    -V|--dssat-version) DSSAT_VERSION=$2; shift 2;;
    -t|--test-installation) TEST_INSTALLATION=true; shift 1;;
    -h|--help|*) usage; exit;;
  esac
done

# set default values when needed
readonly PSIMS_FOLDER=${PSIMS_FOLDER:-/opt/psims}
readonly SWIFT_FOLDER=${SWIFT_FOLDER:-/opt/swift}
readonly DSSAT_FOLDER=${DSSAT_FOLDER:-/opt/dssat}
readonly DSSAT_EXECUTABLE=${DSSAT_EXECUTABLE:-dscsm047}
readonly DSSAT_VERSION=${DSSAT_VERSION:-47}

# check dependencies
[[ ! -n `which git` ]] &&
  report_error "Git does not seem to be installed on your system! Please install it to continue (sudo apt install git)." &&
  exit 1
[[ ! -n `which unzip` ]] &&
  report_error "Unzip does not seem to be installed on your system! Please install it to continue (sudo apt install unzip)." &&
  exit 1
[[ ! -n `which run_dssat` ]] &&
  report_error "DSSAT does not seem to be installed on your system! Please install it to continue (see: https://github.com/danielbonhaure/dssat-installation)." &&
  exit 1

#
#
#

new_script "Instalando dependencias"

# Actualizar repos
new_section "Actualizando repositorios"
sudo apt update

# Instalación de pyhton3
new_section "Instalando python3"
sudo apt install -y python3 python3-dev python3-software-properties; test $? -ne 0 && exit 1

# Instalación de NetCDF
new_section "Instalando NetCDF"
sudo apt install -y netcdf-bin nco libhdf5-dev libnetcdf-dev; test $? -ne 0 && exit 1

# Instalación de Python-NetCDF
new_section "Instalando Python-NetCDF"
sudo apt install -y python3-netcdf4; test $? -ne 0 && exit 1

# Instalación la JVM de Oracle
if [[ ! -n `which java` ]] || [[ ! -n `java -version 2>&1 | grep -w 1.8` ]]; then
  new_section "Instalando JDK 8"
  if [[ `lsb_release -is` == "Debian" ]] && [[ `lsb_release -rs` == 10 ]]; then
    sudo sh -c 'echo "deb http://deb.debian.org/debian/ stretch main" >> /etc/apt/sources.list.d/java-8-debian.list'
    sudo apt update
  fi
  sudo apt install -y openjdk-8-jdk; test $? -ne 0 && exit 1
  sudo update-alternatives --config java
fi

# Instalación de Swift
if [[ ! -n `which swift` ]]; then
  new_section "Instalando Swift 0.95"
  [[ -d $SWIFT_FOLDER ]] && sudo rm -rf $SWIFT_FOLDER
  sudo mkdir $SWIFT_FOLDER
  sudo wget http://swift-lang.org/packages/swift-0.95-RC6.tar.gz
  sudo tar -zxf swift-0.95-RC6.tar.gz
  sudo mv swift-0.95-RC6 $SWIFT_FOLDER/swift-0.95-RC6
  sudo rm -f swift-0.95-RC6.tar.gz
  sudo ln -s $SWIFT_FOLDER/swift-0.95-RC6/bin/swift /usr/bin/swift
  # Fijamos el path a SWIFT_HOME dentro del ejecutable de swift (no lo encuentra solo porque creamos un symlink).
  sudo sed -i 's|SWIFT_HOME=\$.*|SWIFT_HOME='$SWIFT_FOLDER'/swift-0.95-RC6|g' $SWIFT_FOLDER/swift-0.95-RC6/bin/swift
fi

#
#
#

# Instalar pSIMS
new_script "Instalando pSIMS"

# Descargar pSIMS
new_section "Descargando pSIMS"
[[ -d $PSIMS_FOLDER ]] && sudo rm -rf $PSIMS_FOLDER
git clone https://github.com/danielbonhaure/psims.git
test $? -ne 0 && exit 1

# Configurar pSIMS para correr localmente.
new_section "Configurando pSIMS"
sudo mv psims $PSIMS_FOLDER
sudo chown -R "$USER" $PSIMS_FOLDER
mkdir $PSIMS_FOLDER/.workdir
chmod -R 777 $PSIMS_FOLDER/.workdir
mkdir $PSIMS_FOLDER/.taskdir
chmod -R 777 $PSIMS_FOLDER/.taskdir
sed -i '0,/workDir/{s|workDir=.*|workDir='$PSIMS_FOLDER'/.workdir|g}' $PSIMS_FOLDER/conf/swift.properties
sed -i '0,/taskDir/{s|taskDir=.*|taskDir='$PSIMS_FOLDER'/.taskdir|g}' $PSIMS_FOLDER/conf/swift.properties
sed -i 's|/path/to/psims|'$PSIMS_FOLDER'|g' $PSIMS_FOLDER/campaigns/example/junin/mz/params
sed -i 's|MZCER0XX|MZCER0'$DSSAT_VERSION'|g' $PSIMS_FOLDER/campaigns/example/junin/mz/params
sed -i 's|DSCSM0XX|'$DSSAT_FOLDER'/'$DSSAT_EXECUTABLE'|g' $PSIMS_FOLDER/campaigns/example/junin/mz/params
sed -i 's|/path/to/dssat|'$DSSAT_FOLDER'|g' $PSIMS_FOLDER/campaigns/example/junin/mz/params
sed -i 's|--dssat_version XX|--dssat_version '$DSSAT_VERSION'|g' $PSIMS_FOLDER/campaigns/example/junin/mz/params
if [[ ! `grep -w UAIC10 $DSSAT_FOLDER/Genotype/MZCER0${DSSAT_VERSION}.CUL` ]]; then
  sudo sh -c 'printf "\n! Added for test pSIMS\n" >> '$DSSAT_FOLDER'/Genotype/MZCER0'$DSSAT_VERSION'.CUL'
  sudo sh -c 'echo "UAIC10 DK 682   120 GSP     . IB0001 245.0 0.000 820.0 950.0  7.50 45.00" >> '$DSSAT_FOLDER'/Genotype/MZCER0'$DSSAT_VERSION'.CUL'
fi

if [[ $TEST_INSTALLATION ]]; then
  new_section "Probando pSIMS"
  # Para probar la instalación seguir el tutorial en:
  # https://github.com/danielbonhaure/psims/blob/master/campaigns/example/junin/README.md
  DIR=$(pwd); cd $PSIMS_FOLDER
  ./psims -s local -p ./campaigns/example/junin/mz/params -c ./campaigns/example/junin/mz -g ./campaigns/example/junin/gridList.txt
  sudo rm -rf run001;  cd $DIR; unset DIR
fi

#
#
#

rm ${gutils}

#
#
#
