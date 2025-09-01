# Deploying

- Cannot just pip install on your Mac/Windows — the binaries won’t work in Lambda.
- You need to build them inside an Amazon Linux 2 environment

✅ How to use

Save as build_layer.sh

Make executable:

chmod +x build_layer.sh


Run it:

./build_layer.sh


You’ll get a opencv-numpy.zip in your current directory.