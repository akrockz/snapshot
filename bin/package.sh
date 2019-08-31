#!/bin/bash

set -e

echo "core-snapshot package script running."

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" # this script's directory
echo "DIR=${DIR}"
REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"  # project folder
echo "REPO_DIR=${REPO_DIR}"
STAGING_DIR="${DIR}/../_staging"
echo "STAGING_DIR=${STAGING_DIR}"
LAMBDA_DIR="${DIR}/../lambdas"
echo "LAMBDA_DIR=${LAMBDA_DIR}"

# Setup, cleanup.
cd $DIR
mkdir -p $STAGING_DIR # files dir for lambdas
rm -rf $STAGING_DIR/*

# Copy deployspec and CFN templates into staging folder.
cp -pr $DIR/../*.yaml $STAGING_DIR/

# Install dependencies for all lambdas.
cd $REPO_DIR
python3 $REPO_DIR/bin/install-lambda-dependencies.py

# Create Lambda zip packages
cd $LAMBDA_DIR
for LAMBDA_NAME in */; do
    LAMBDA_NAME=${LAMBDA_NAME%*/}
    if [ $LAMBDA_NAME != "_common" ]; then
	    echo "Packaging lambda $LAMBDA_NAME"
	    cd "$LAMBDA_DIR/$LAMBDA_NAME"
	    >/dev/null zip -9 -r $STAGING_DIR/$LAMBDA_NAME.zip * -x \*.pyc \*.md \*.zip \*.log \*__pycache__\* \*.so
	fi
done

echo "core-snapshot package step complete, run.sh can be executed now."
