[app]
title = Maher Umar POS
package.name = maherumarpos
package.domain = com.maherumar
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas,txt,md,sql
version = 0.1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 35
android.minapi = 23
android.archs = arm64-v8a
android.accept_sdk_license = True
p4a.branch = v2026.05.09
# Cloud sync is not enabled in this starter. Add Supabase client only after auth is implemented.
[buildozer]
log_level = 2
warn_on_root = 1
