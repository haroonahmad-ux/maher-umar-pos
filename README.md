# Maher Umar POS — Android starter

This is an Android-friendly Kivy starter derived from the POS workflow requirements. It currently provides:
- Mobile dashboard
- Product/inventory creation and listing
- Single-product sales recording with stock deduction
- Customer name/phone fields on sales
- Expense recording and listing
- Basic summary reports
- Local SQLite storage in the app's private data directory

## Build APK with GitHub Actions
1. Upload these files into the root of `haroonahmad-ux/maher-umar-pos`:
   - `main.py`
   - `requirements.txt`
   - `buildozer.spec`
   - `.github/workflows/build-apk.yml`
2. Commit the files.
3. Open the repository's **Actions** tab.
4. Run **Build Android APK** (or wait for a push-triggered run).
5. When successful, open the workflow run and download the `maher-umar-pos-debug-apk` artifact. Extract the ZIP to get the APK and install it on your Android phone.

## Important limitations
- This is a new Android UI starter, not a 1:1 port of every existing CLI feature.
- It uses local SQLite only. It is **not yet connected to Supabase**.
- PDF invoice generation, original discount rules, udhaar book details, backups, and full sales-history profit calculations have not yet been ported.
- No release signing is configured; this produces a debug APK artifact for testing, not a Play Store release.
- Test with sample data before using for live shop records. Do not put Supabase service-role keys in the app.
