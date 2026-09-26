from pathlib import Path

p=Path("app/src/main/java/com/negmdiarb/app/MainActivity.java")
s=p.read_text(encoding="utf-8")

def need(old,new,label):
    global s
    if old not in s: raise SystemExit("MISSING: "+label)
    s=s.replace(old,new,1)

# ---- 1) Stop duplicate/late business renders caused by overlapping Firestore reads. ----
need('boolean adminMode=false; String staffRole=""; String offerStartDate="",offerEndDate";',
     'boolean adminMode=false; String staffRole=""; String offerStartDate="",offerEndDate";',
     'sanity marker') if False else None

# Add a generation token. Every new load invalidates older callbacks.
need('boolean adminReturnToPanel=false;',
     'boolean adminReturnToPanel=false; int businessLoadGeneration=0;',
     'business load generation')

# setup() was calling loadBusinesses again after initFirebase() already started it.
s=s.replace('        show(homePanel);\n        if(auth!=null&&db!=null){loadFavorites();loadBusinesses();}\n',
            '        show(homePanel);\n',1)

# Every load gets a unique generation; stale callbacks cannot append old rows.
need('void loadBusinesses(){\n        if(db==null)return; businessList.removeAllViews();',
     'void loadBusinesses(){\n        if(db==null)return; final int generation=++businessLoadGeneration; businessList.removeAllViews();',
     'load generation start')
need('db.collection("businesses").whereEqualTo("status","approved").whereEqualTo("active",true).limit(60).get().addOnSuccessListener(s->{',
     'db.collection("businesses").whereEqualTo("status","approved").whereEqualTo("active",true).limit(60).get().addOnSuccessListener(s->{\n            if(generation!=businessLoadGeneration)return;',
     'stale callback guard')

# ---- 2) Admin review notifications: actually start the listener and do not spam existing items. ----
need('com.google.firebase.firestore.ListenerRegistration adminNotificationListener;',
     'com.google.firebase.firestore.ListenerRegistration adminNotificationListener; boolean adminNotificationBaselineReady=false;',
     'notification baseline field')

old='''adminNotificationListener=db.collection("adminNotifications").whereEqualTo("status","pending").addSnapshotListener((snap,e)->{
            if(e!=null||snap==null)return;
            if(!snap.isEmpty())postAdminLocalNotification("نجم ديرب — مراجعة مطلوبة","يوجد "+snap.size()+" عنصر يحتاج مراجعة.");
            refreshAdminBadges();
        });'''
new='''adminNotificationBaselineReady=false;
        adminNotificationListener=db.collection("adminNotifications").whereEqualTo("status","pending").addSnapshotListener((snap,e)->{
            if(e!=null||snap==null)return;
            if(!adminNotificationBaselineReady){
                adminNotificationBaselineReady=true;
                refreshAdminBadges();
                return;
            }
            for(DocumentChange ch:snap.getDocumentChanges()){
                if(ch.getType()==DocumentChange.Type.ADDED){
                    DocumentSnapshot d=ch.getDocument();
                    postAdminLocalNotification(
                        safe(d.getString("title")).isEmpty()?"نجم ديرب — مراجعة مطلوبة":safe(d.getString("title")),
                        safe(d.getString("body")).isEmpty()?"يوجد عنصر جديد يحتاج مراجعة.":safe(d.getString("body"))
                    );
                }
            }
            refreshAdminBadges();
        });'''
need(old,new,'notification listener body')

# Start listener whenever an admin session is established.
s=s.replace('applyRolePermissions();loadRoleData();',
            'applyRolePermissions();loadRoleData();if(isMainAdmin()){startAdminNotificationListener();refreshAdminBadges();}',
            2)

# Also start it for an already authenticated admin restored at app launch.
s=s.replace('adminMode=true;staffRole=role;applyRolePermissions();',
            'adminMode=true;staffRole=role;applyRolePermissions();if(isMainAdmin()){startAdminNotificationListener();refreshAdminBadges();}',
            1)

# ---- 3) Owner-account creation: make the failure point visible and ensure the selected business is active. ----
s=s.replace('db.collection("businesses").whereEqualTo("status","approved").limit(300).get().addOnSuccessListener(bs->',
            'db.collection("businesses").whereEqualTo("status","approved").whereEqualTo("active",true).limit(150).get().addOnSuccessListener(bs->',
            1)

# Do not silently dismiss the owner dialog until the account + Firestore binding both succeed.
old2='''createAuthUser(email,pass,m->{m.put("role","owner");m.put("displayName",ownerName);m.put("email",email);m.put("phone",ph.getText().toString().trim());m.put("businessName",safe(b.getString("name")));m.put("businessId",bid);m.put("enabled",true);m.put("permissions",Arrays.asList("owner_profile_edit_request","owner_offer_create","owner_requests_view"));m.put("createdAt",FieldValue.serverTimestamp());},"تم إنشاء حساب صاحب المنشأة وربطه."); dialog.dismiss();'''
new2='''createAuthUser(email,pass,m->{m.put("role","owner");m.put("displayName",ownerName);m.put("email",email);m.put("phone",ph.getText().toString().trim());m.put("businessName",safe(b.getString("name")));m.put("businessId",bid);m.put("enabled",true);m.put("permissions",Arrays.asList("owner_profile_edit_request","owner_offer_create","owner_requests_view"));m.put("createdAt",FieldValue.serverTimestamp());},"تم إنشاء حساب صاحب المنشأة وربطه.",()->dialog.dismiss());'''
need(old2,new2,'owner dialog success callback')

# Replace createAuthUser signature with a success callback, keeping all existing behavior.
need('void createAuthUser(String email,String password,UserMapBuilder builder,String ok){',
     'void createAuthUser(String email,String password,UserMapBuilder builder,String ok){ createAuthUser(email,password,builder,ok,null); }\n    void createAuthUser(String email,String password,UserMapBuilder builder,String ok,Runnable onSuccess){',
     'createAuthUser overload')

need('toast("✅ "+ok);\n                if("owner".equals(role))loadOwners();',
     'toast("✅ "+ok);\n                if("owner".equals(role))loadOwners();\n                if(onSuccess!=null)onSuccess.run();',
     'owner success hook')

p.write_text(s,encoding="utf-8")
print("V34 PATCH OK")
