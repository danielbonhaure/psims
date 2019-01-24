#!/usr/bin/env bash
#
# Download this file and execute it!
# wget https://raw.githubusercontent.com/danielbonhaure/psims/master/install.sh --output-document=install-psims.sh
#

sudo echo ""; if [[ $? -ne 0 ]] ; then exit 1; fi
wget --quiet https://raw.githubusercontent.com/danielbonhaure/psims/master/gutils.sh --output-document=gutils.sh
source gutils.sh; if [[ $? -ne 0 ]] ; then exit 1; fi

#
#
#


new_script "Instalando dependencias"


#if ! hash ifort 2>/dev/null; then
#    report_error "No se encuentra ifort (Intel Fortran Compiler) en PATH."
#    exit 1
#fi


# Actualizar repos
new_section "Actualizando repositorios"
sudo apt update

# Instalación de pyhton3
new_section "Instalando python3"
sudo apt install -y python3 python3-dev python3-software-properties

# Instalación de NetCDF
new_section "Instalando NetCDF"
sudo apt install -y netcdf-bin nco libhdf5-dev libnetcdf-dev

# Instalación de Python-NetCDF
new_section "Instalando Python-NetCDF"
sudo apt install -y python3-netcdf4 

# Instalación la JVM de Oracle
new_section "Instalando la JVM de Oracle"
sudo add-apt-repository -y ppa:webupd8team/java
sudo apt update
sudo apt install -y oracle-java8-installer

# Instalación de Swift
new_section "Instalando Swift 0.95"
if [ -d /opt/swift ]; then
    sudo rm -rf /opt/swift
fi
sudo mkdir /opt/swift
sudo wget http://swift-lang.org/packages/swift-0.95-RC6.tar.gz
sudo tar -zxf swift-0.95-RC6.tar.gz
sudo mv swift-0.95-RC6 /opt/swift/swift-0.95-RC6
sudo rm -f swift-0.95-RC6.tar.gz
sudo ln -s /opt/swift/swift-0.95-RC6/bin/swift /usr/bin/swift
# Fijamos el path a SWIFT_HOME dentro del ejecutable de swift (no lo encuentra solo porque creamos un symlink).
sudo sed -i 's/SWIFT_HOME=\$.*/SWIFT_HOME=\/opt\/swift\/swift-0.95-RC6/' /opt/swift/swift-0.95-RC6/bin/swift

# Compilar DSSAT
#new_section "Compilando DSSAT"
#sudo tar -zxf dssat-csm-4.6.0.21.tar.gz
#sudo chmod -R 777 dssat-csm-4.6.0.21
#cd dssat-csm-4.6.0.21/
#make all
#
#if [ ! -f DSCSM046.EXE ]; then
#    report_error "DSSAT compilation failed."
#    exit 1
#fi
#
#mv DSCSM046.EXE ../DSCSM046
#cd ..
#rm -rf dssat-csm-4.6.0.21
#sudo chmod 775 DSCSM046

# Instalar DSSAT
new_section "Instalando DSSAT"
sudo apt install -y unzip
if [ ! -f DSCSM046 ] || [ ! -f DSCSM461 ]; then
    if [ -f DSSAT.zip ]; then
        sudo unzip -o DSSAT.zip
    elif [ -f dssat.zip ]; then
        sudo unzip -o dssat.zip
    fi
    sudo chmod 775 DSCSM*
fi


# Instalar pSIMS
new_script "Instalando pSIMS"


# Instalar git
new_section "Instalando Git"
sudo apt install -y git

# Descargar pSIMS
new_section "Descargando pSIMS"
if [ -d /opt/psims ]; then
    sudo rm -rf /opt/psims
fi
git clone https://github.com/danielbonhaure/psims.git

# Configurar pSIMS para correr localmente.
new_section "Configurando pSIMS"
if [ -f DSCSM046 ]; then
    mv DSCSM046 psims/bin/DSCSM046
fi
if [ -f DSCSM461 ]; then
    mv DSCSM461 psims/bin/DSCSM461
fi
sudo mv psims /opt/psims
sudo chown -R "$USER" /opt/psims
mkdir /opt/psims/.workdir
chmod -R 777 /opt/psims/.workdir
mkdir /opt/psims/.taskdir
chmod -R 777 /opt/psims/.taskdir
sed -i '0,/workDir/{s/workDir=.*/workDir=\/opt\/psims\/.workdir/}' /opt/psims/conf/swift.properties
sed -i '0,/taskDir/{s/taskDir=.*/taskDir=\/opt\/psims\/.taskdir/}' /opt/psims/conf/swift.properties
# Para probar la instalación seguir el tutorial en:
# https://github.com/schmidtfederico/psims/tree/master/campaigns/example/junin
sed -i 's/\/path\/to\/psims-schmidtfederico/\/opt\/psims/' /opt/psims/campaigns/example/junin/mz/params
# DIR=$(pwd); cd /opt/psims
# ./psims -s local -p ./campaigns/example/junin/mz/params -c ./campaigns/example/junin/mz -g ./campaigns/example/junin/gridList.txt
# cd $DIR; unset DIR

if [ ! -f /opt/psims/bin/DSCSM046 ]; then
    report_warning "DSSAT executable not found (DSCSM046), please place it in the /opt/psims/bin folder!!"
fi

#
#
#

rm gutils.sh
