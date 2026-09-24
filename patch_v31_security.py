from pathlib import Path
p=Path("app/src/main/java/com/negmdiarb/app/MainActivity.java")
s=p.read_text(encoding="utf-8")

# Bind the main admin role to the first Android device that successfully uses it.
old='boolean isMainAdmin(){return "admin".equals(staffRole);}'
new='''String currentAdminDeviceId(){
        try{
            String id=android.provider.Settings.Secure.getString(getContentResolver(),android.provider.Settings.Secure.ANDROID_ID);
            return id==null?"":id;
        }catch(Exception e){return "";}
    }
    boolean isMainAdmin(){
        if(!"admin".equals(staffRole))return false;
        String device=currentAdminDeviceId();
        if(device.isEmpty())return false;
        String bound=adminPrefs().getString("admin_device_id","");
        if(bound.isEmpty()){
            adminPrefs().edit().putString("admin_device_id",device).apply();
            return true;
        }
        return bound.equals(device);
    }'''
if old in s:
    s=s.replace(old,new,1)
elif "String currentAdminDeviceId()" not in s:
    raise SystemExit("isMainAdmin marker not found")

# Alternative admin entry: long press on the home status area, in addition to the existing 7-tap trigger.
needle='''findViewById(R.id.btnStaffPublicLogin).setOnClickListener(v->staffLogin());'''
if needle in s and 'homeStatus.setOnLongClickListener' not in s:
    s=s.replace(needle,needle+'''
        homeStatus.setOnLongClickListener(v->{staffLogin();return true;});
        homeStatus.setOnClickListener(v->{
            adminTapCount++;
            if(adminTapCount>=7){adminTapCount=0;staffLogin();}
        });''',1)

# Keep device binding when logging out. Session state can be reset, but the enrolled device must remain.
s=s.replace('adminPrefs().edit().clear().apply();','adminPrefs().edit().remove("admin_session").apply();')

# Add a clear message if credentials are correct on a different device.
if 'هذا الجهاز غير مسجل للإدارة' not in s:
    s=s.replace('if(!isMainAdmin()){toast("المدير الرئيسي فقط.");return;}',
                'if(!isMainAdmin()){toast("هذا الجهاز غير مسجل للإدارة.");return;}',1)

p.write_text(s,encoding="utf-8")
print("ADMIN DEVICE BINDING PATCH OK")
