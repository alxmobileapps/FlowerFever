"""Use Google's explicit button flow for Flower Fever's user-initiated sign-in.
Pinned to authentication 7.5.0; fail the build if upstream code changes.
"""
import pathlib

def patch(source):
    if "GetSignInWithGoogleOption googleIdOption" in source:
        return source
    replacements = [
        ("import com.google.android.libraries.identity.googleid.GetGoogleIdOption;",
         "import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption;"),
        ("""GetGoogleIdOption googleIdOption = new GetGoogleIdOption.Builder()
                // Your server's client ID, not your Android client ID
                .setServerClientId(pluginImplementation.getPlugin().getContext().getString(R.string.default_web_client_id))
                // Show all accounts on the device (not just the accounts that have been used previously)
                .setFilterByAuthorizedAccounts(false)
                .build();""",
         """GetSignInWithGoogleOption googleIdOption = new GetSignInWithGoogleOption.Builder(
                pluginImplementation.getPlugin().getContext().getString(R.string.default_web_client_id)
            ).build();"""),
        ("""credentialManager.getCredentialAsync(
                pluginImplementation.getPlugin().getContext(),""",
         """credentialManager.getCredentialAsync(
                pluginImplementation.getPlugin().getActivity(),""")
    ]
    for old, new in replacements:
        if source.count(old) != 1:
            raise RuntimeError("Google sign-in plugin changed; review button-flow patch before building")
        source = source.replace(old, new)
    return source

if __name__ == "__main__":
    target = pathlib.Path("node_modules/@capacitor-firebase/authentication/android/src/main/java/io/capawesome/capacitorjs/plugins/firebase/authentication/handlers/GoogleAuthProviderHandler.java")
    target.write_text(patch(target.read_text()))
    print("Google sign-in: explicit account button flow enabled")
