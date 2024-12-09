console.log("custom-loader.js");

// custom-loader.mjs
export async function resolve(specifier, context, defaultResolve) {
    console.log("resolve", specifier);
    if (specifier === "lodash") {
        return { url: `file://${process.cwd()}/patched-lodash.mjs` };
    }
    return defaultResolve(specifier, context, defaultResolve);
}
