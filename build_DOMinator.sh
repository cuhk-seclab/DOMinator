#!/bin/bash - 
VERSION=88.0.4303.1
NTHREADS=32
BUILD_DIR=DOMinator
PATCH_DIR=Patch

is_darwin=0
is_linux=0
UNAME=$(uname)
case $UNAME in
    "Darwin") is_darwin=1;;
    "Linux") is_linux=1;;
esac

fetch_source ()
{
  git config --global core.precomposeUnicode true
  fetch --nohooks chromium
  cd $CHROMIUM/src
  git checkout -b dev $VERSION
}

gclient_sync ()
{
  gclient sync --with_branch_heads --jobs $NTHREADS
}

install_deps ()
{
  if [ $is_darwin = 1 ]; then
    xcode-select --install # You can comment this line if you have installed XCode already
    if hash port 2>/dev/null; then
      sudo port install wget ccache docbook2X autoconf automake libtool
      sudo mkdir -p /usr/local/opt/lzo/lib/
      cd /usr/local/opt/lzo/lib/
      sudo ln -s /opt/local/lib/liblzo2.2.dylib . 2>/dev/null
    elif hash brew 2>/dev/null; then
      brew install wget ccache autoconf automake libtool
      echo ""
    else
      echo "Please install HomeBrew or MacPorts before you proceed!"
      exit 1
    fi

  elif [ $is_linux = 1 ]; then
    sudo apt-get install ccache
    echo ""
    cd $CHROMIUM/src
    sudo ./build/install-build-deps.sh --no-syms --no-arm --no-chromeos-fonts --no-nacl
  fi
}

run_hooks ()
{
  cd $CHROMIUM/src
  gclient runhooks
}

apply_patch ()
{
  cd $CHROMIUM/src/third_party/blink/renderer && patch -p1 < $ROOT/$PATCH_DIR/cpp.patch
}

conf_build ()
{
  cd $CHROMIUM/src
  mkdir -p out/$BUILD_DIR
  gn gen out/$BUILD_DIR '--args=cc_wrapper="ccache" use_jumbo_build=false is_debug=false enable_nacl=false'
}

build ()
{
  export CCACHE_BASEDIR=$CHROMIUM
  cd $CHROMIUM/src
  time autoninja -C out/$BUILD_DIR chrome
}


mkdir -p chromium
ROOT=$PWD
cd chromium
CHROMIUM=$PWD

# Invoke functions
fetch_source
gclient_sync
install_deps
apply_patch
run_hooks
conf_build
build
