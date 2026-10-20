/* Offline WinPR/shim ABI smoke test. No credentials or packets leave the process. */
#define WIN32_LEAN_AND_MEAN
#define SECURITY_WIN32 1
#include <windows.h>
#include <sspi.h>
#include <stdio.h>
#include <string.h>

static int probe_a(HMODULE module)
{
    FARPROC address = GetProcAddress(module, "InitSecurityInterfaceA");
    INIT_SECURITY_INTERFACE_A init = NULL;
    memcpy(&init, &address, sizeof(init));
    PSecurityFunctionTableA api = init ? init() : NULL;
    if (!api) {
        fprintf(stderr, "ANSI SSPI table unavailable\n");
        return 1;
    }
    SEC_WINNT_AUTH_IDENTITY_A identity = {
        (unsigned char *)"fixture", 7, (unsigned char *)"TEST", 4,
        (unsigned char *)"fixture-only", 12, SEC_WINNT_AUTH_IDENTITY_ANSI
    };
    CredHandle credential = {0};
    CtxtHandle context = {0};
    TimeStamp expiry = {0};
    SECURITY_STATUS status = api->AcquireCredentialsHandleA(
        NULL, "Negotiate", SECPKG_CRED_OUTBOUND, NULL, &identity, NULL, NULL,
        &credential, &expiry);
    if (status != SEC_E_OK) {
        fprintf(stderr, "ANSI acquire status=0x%08lx\n", (unsigned long)status);
        return 1;
    }
    unsigned char storage[65536] = {0};
    SecBuffer token = {sizeof(storage), SECBUFFER_TOKEN, storage};
    SecBufferDesc output = {SECBUFFER_VERSION, 1, &token};
    ULONG attributes = 0;
    status = api->InitializeSecurityContextA(
        &credential, NULL, "TERMSRV/fixture.invalid",
        ISC_REQ_CONFIDENTIALITY | ISC_REQ_CONNECTION,
        0, SECURITY_NATIVE_DREP, NULL, 0, &context, &output, &attributes, &expiry);
    int present = token.cbBuffer > 0 && token.cbBuffer < sizeof(storage);
    int failed = status != SEC_I_CONTINUE_NEEDED || !present;
    printf("ANSI negotiate status=0x%08lx token-present=%d\n",
           (unsigned long)status, present);
    if (context.dwLower || context.dwUpper)
        failed |= api->DeleteSecurityContext(&context) != SEC_E_OK;
    failed |= api->FreeCredentialsHandle(&credential) != SEC_E_OK;
    return failed;
}

static int probe_w(HMODULE module)
{
    FARPROC address = GetProcAddress(module, "InitSecurityInterfaceW");
    INIT_SECURITY_INTERFACE_W init = NULL;
    memcpy(&init, &address, sizeof(init));
    PSecurityFunctionTableW api = init ? init() : NULL;
    if (!api) {
        fprintf(stderr, "Unicode SSPI table unavailable\n");
        return 1;
    }
    SEC_WINNT_AUTH_IDENTITY_W identity = {
        (unsigned short *)L"fixture", 7, (unsigned short *)L"TEST", 4,
        (unsigned short *)L"fixture-only", 12, SEC_WINNT_AUTH_IDENTITY_UNICODE
    };
    CredHandle credential = {0};
    CtxtHandle context = {0};
    TimeStamp expiry = {0};
    SECURITY_STATUS status = api->AcquireCredentialsHandleW(
        NULL, L"Negotiate", SECPKG_CRED_OUTBOUND, NULL, &identity, NULL, NULL,
        &credential, &expiry);
    if (status != SEC_E_OK) {
        fprintf(stderr, "Unicode acquire status=0x%08lx\n", (unsigned long)status);
        return 1;
    }
    unsigned char storage[65536] = {0};
    SecBuffer token = {sizeof(storage), SECBUFFER_TOKEN, storage};
    SecBufferDesc output = {SECBUFFER_VERSION, 1, &token};
    ULONG attributes = 0;
    status = api->InitializeSecurityContextW(
        &credential, NULL, L"TERMSRV/fixture.invalid",
        ISC_REQ_CONFIDENTIALITY | ISC_REQ_CONNECTION,
        0, SECURITY_NATIVE_DREP, NULL, 0, &context, &output, &attributes, &expiry);
    int present = token.cbBuffer > 0 && token.cbBuffer < sizeof(storage);
    int failed = status != SEC_I_CONTINUE_NEEDED || !present;
    printf("Unicode negotiate status=0x%08lx token-present=%d\n",
           (unsigned long)status, present);
    if (context.dwLower || context.dwUpper)
        failed |= api->DeleteSecurityContext(&context) != SEC_E_OK;
    failed |= api->FreeCredentialsHandle(&credential) != SEC_E_OK;
    return failed;
}

int main(int argc, char **argv)
{
    if (argc != 2 || strlen(argv[1]) != 40)
        return 2;
    HMODULE winpr = LoadLibraryA("libwinpr3.dll");
    if (!winpr) {
        fprintf(stderr, "WinPR load failed: %lu\n", (unsigned long)GetLastError());
        return 1;
    }
    typedef const char *(*revision_fn)(void);
    FARPROC address = GetProcAddress(winpr, "winpr_get_build_revision");
    revision_fn revision = NULL;
    memcpy(&revision, &address, sizeof(revision));
    const char *reported = revision ? revision() : "";
    size_t length = strlen(reported);
    printf("WinPR revision=%s\n", reported);
    if (length < 8 || length > 40 || strncmp(reported, argv[1], length) != 0) {
        fprintf(stderr, "WinPR source revision mismatch\n");
        return 1;
    }
    HMODULE module = LoadLibraryA("winpr-sspi-shim.dll");
    if (!module) {
        fprintf(stderr, "shim load failed: %lu\n", (unsigned long)GetLastError());
        return 1;
    }
    int result_a = probe_a(module);
    int result_w = probe_w(module);
    FreeLibrary(module);
    FreeLibrary(winpr);
    return result_a || result_w;
}
