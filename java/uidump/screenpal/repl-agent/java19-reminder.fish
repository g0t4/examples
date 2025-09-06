# SOURCE ME

# FYI if you build with maven this won't matter then b/c pom.xml has <maven.compiler.release>

echo "## version BEFORE:" 
java --version

# reminder to use 19 for this setup to be compat with ScreenPal's JRE
export PATH="$(/usr/libexec/java_home -v 19)/bin:$PATH"

echo
echo "## version AFTER:" 
java --version
