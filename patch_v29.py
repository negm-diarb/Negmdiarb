from pathlib import Path
import re, shutil

ROOT = Path(".")
JAVA = ROOT / "app/src/main/java/com/negmdiarb/app/MainActivity.java"
LAYOUT = ROOT / "app/src/main/res/layout/activity_main.xml"
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
ICON_SRC = Path(__file__).resolve().parent / "assets" / "negm_icon_user.jpg"

def replace_method(src, start_sig, end_sig, repl):
    a = src.index(start_sig)
    b = src.index(end_sig, a)
    return src[:a] + repl + src[b:]

s = JAVA.read_text(encoding="utf-8")

# V29 state used to return to the exact admin section after add/edit screens.
s = s.replace(
    'boolean adminMode=false; String staffRole=""; String offerStartDate="",offerEndDate="";',
    'boolean adminMode=false; String staffRole=""; String offerStartDate="",offerEndDate="";\n    int adminReturnSection=0;'
)

# Better establishment-card actions: two clean rows instead of six cramped equal-width buttons.
s = replace_method(s, '    void addBusinessCard(DocumentSnapshot d){', '    void toggleFavorite',
r'''    void addBusinessCard(DocumentSnapshot d){
        LinearLayout card=box();
        String n=safe(d.getString("name"));
        double avg=num(d,"ratingAvg");
        long cnt=d.getLong("ratingCount")==null?0:d.getLong("ratingCount");
        String badge=truth(d,"featured")?" ⭐ مميز":"";
        TextView title=tv("🏪 "+n+badge);
        title.setTextSize(18);
        title.setTypeface(null,android.graphics.Typeface.BOLD);
        title.setTextColor(Color.rgb(16,42,102));
        card.addView(title);

        TextView meta=tv("📂 "+safe(d.getString("category")));
        meta.setTextSize(13);
        meta.setTextColor(Color.rgb(104,115,134));
        card.addView(meta);

        card.addView(buildStarsRow(avg,cnt,false));

        String desc=safe(d.getString("description"));
        if(desc.length()>100)desc=desc.substring(0,100)+"…";
        TextView loc=tv("📍 "+safe(d.getString("address"))+(desc.isEmpty()?"":"\n"+desc));
        loc.setTextSize(14);
        loc.setTextColor(Color.rgb(53,64,83));
        card.addView(loc);

        LinearLayout primary=new LinearLayout(this);
        primary.setOrientation(LinearLayout.HORIZONTAL);
        primary.setGravity(Gravity.CENTER_VERTICAL);
        Button mapBtn=btn("🗺️ خريطة"),callBtn=btn("📞 اتصال"),waBtn=btn("💬 واتساب");
        Button[] pbtn={mapBtn,callBtn,waBtn};
        for(Button b:pbtn){
            b.setTextSize(12);
            b.setAllCaps(false);
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(48),1);
            lp.setMargins(dp(2),dp(2),dp(2),dp(2));
            primary.addView(b,lp);
        }
        card.addView(primary);

        LinearLayout secondary=new LinearLayout(this);
        secondary.setOrientation(LinearLayout.HORIZONTAL);
        secondary.setGravity(Gravity.CENTER_VERTICAL);
        Button rateBtn=btn("⭐ تقييم"),favBtn=btn(favoriteIds.contains(d.getId())?"♥ حفظ":"♡ حفظ"),shareBtn=btn("↗ مشاركة");
        Button[] sbtn={rateBtn,favBtn,shareBtn};
        for(Button b:sbtn){
            b.setTextSize(12);
            b.setAllCaps(false);
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(44),1);
            lp.setMargins(dp(2),0,dp(2),dp(2));
            secondary.addView(b,lp);
        }
        card.addView(secondary);

        card.setOnClickListener(v->{logEvent("businessViews",d.getId());showBusinessDetails(d);});
        mapBtn.setOnClickListener(v->{logEvent("mapClicks",d.getId());openMap(d);});
        callBtn.setOnClickListener(v->{logEvent("callClicks",d.getId());call(d.getString("phone"));});
        waBtn.setOnClickListener(v->{logEvent("whatsappClicks",d.getId());wa(d.getId(),d.getString("whatsapp"));});
        rateBtn.setOnClickListener(v->showRatingDialog(d.getId()));
        favBtn.setOnClickListener(v->toggleFavorite(d.getId(),favBtn));
        shareBtn.setOnClickListener(v->shareBusiness(d));
        businessList.addView(card);
    }

''')

# Admin rating list now resolves the actual establishment name before displaying the item.
s = replace_method(s, '    void loadRatings(){', '    void approveRating',
r'''    void loadRatings(){
        adminRatingList.removeAllViews();
        if(!isMainAdmin()){addText(adminRatingList,"التقييمات متاحة للمدير الرئيسي فقط.");return;}
        db.collection("businesses").limit(500).get().addOnSuccessListener(bs->{
            HashMap<String,String> names=new HashMap<>();
            for(DocumentSnapshot b:bs)names.put(b.getId(),safe(b.getString("name")));
            db.collection("ratings").limit(300).get().addOnSuccessListener(snap->{
                if(snap.isEmpty()){addText(adminRatingList,"لا توجد تقييمات.");return;}
                for(DocumentSnapshot d:snap){
                    Long stars=d.getLong("stars");
                    String bid=safe(d.getString("businessId"));
                    String businessName=names.containsKey(bid)?names.get(bid):"منشأة غير موجودة";
                    String status=safe(d.getString("status"));
                    LinearLayout c=box();
                    TextView head=tv("🏪 "+businessName);
                    head.setTextSize(17);
                    head.setTypeface(null,android.graphics.Typeface.BOLD);
                    head.setTextColor(Color.rgb(16,42,102));
                    c.addView(head);
                    c.addView(tv("⭐ "+(stars==null?"":stars)+" من 5\n"+safe(d.getString("text"))+"\nالحالة: "+status));
                    c.addView(tv("🆔 "+bid));
                    LinearLayout a=new LinearLayout(this);
                    Button b=btn("pending".equals(status)?"✅ اعتماد":"🗑️ حذف");
                    a.addView(b);
                    c.addView(a);
                    b.setOnClickListener(v->{
                        if("pending".equals(d.getString("status")))approveRating(d);
                        else d.getReference().delete().addOnSuccessListener(x->loadRatings());
                    });
                    adminRatingList.addView(c);
                }
            }).addOnFailureListener(e->addText(adminRatingList,"تعذر تحميل التقييمات: "+safe(e.getMessage())));
        }).addOnFailureListener(e->addText(adminRatingList,"تعذر تحميل أسماء المنشآت: "+safe(e.getMessage())));
    }

''')

# Back navigation is context-aware for admin add/edit and offer screens.
s = replace_method(s, '    void installBackHandler(){', '    void clearForm',
r'''    void installBackHandler(){
        getOnBackPressedDispatcher().addCallback(this,new OnBackPressedCallback(true){
            @Override public void handleOnBackPressed(){
                if(addPanel.getVisibility()==View.VISIBLE){
                    if(adminMode){returnToAdmin();}
                    else showHome();
                    return;
                }
                if(offersPanel.getVisibility()==View.VISIBLE){
                    if(adminMode){returnToAdmin();}
                    else showHome();
                    return;
                }
                if(adminPanel.getVisibility()==View.VISIBLE){
                    new AlertDialog.Builder(MainActivity.this)
                        .setTitle("العودة من لوحة المدير")
                        .setMessage("هل تريد الخروج من لوحة المدير والعودة إلى الصفحة الرئيسية العادية؟")
                        .setNegativeButton("إلغاء",null)
                        .setPositiveButton("العودة للرئيسية",(d,w)->showHome())
                        .show();
                    return;
                }
                if(homePanel.getVisibility()==View.VISIBLE){
                    new AlertDialog.Builder(MainActivity.this)
                        .setTitle("الخروج من نجم ديرب")
                        .setMessage("هل تريد الخروج من التطبيق؟")
                        .setNegativeButton("إلغاء",null)
                        .setPositiveButton("خروج",(d,w)->finish())
                        .show();
                }else{
                    showHome();
                }
            }
        });
    }

''')

# Add a clean return helper before the existing dp helper.
marker='    int dp(int v){'
helpers=r'''    void returnToAdmin(){
        if(!adminMode){showHome();return;}
        show(adminPanel);
        if(adminReturnSection!=0){
            openAdminSection(adminReturnSection);
        }
        refreshAdminBadges();
    }

    void createAdminNotification(String type,String businessId,String title,String body){
        if(db==null)return;
        Map<String,Object> n=new HashMap<>();
        n.put("type",type);
        n.put("businessId",businessId==null?"":businessId);
        n.put("title",title);
        n.put("body",body);
        n.put("status","pending");
        n.put("createdAt",FieldValue.serverTimestamp());
        n.put("uid",auth!=null&&auth.getCurrentUser()!=null?auth.getCurrentUser().getUid():"");
        db.collection("adminNotifications").add(n);
    }

    void initAdminNotifications(){
        if(android.os.Build.VERSION.SDK_INT>=26){
            android.app.NotificationManager nm=(android.app.NotificationManager)getSystemService(NOTIFICATION_SERVICE);
            if(nm!=null){
                android.app.NotificationChannel ch=new android.app.NotificationChannel("admin_review","مراجعات نجم ديرب",android.app.NotificationManager.IMPORTANCE_HIGH);
                ch.setDescription("تنبيهات الطلبات التي تحتاج مراجعة الإدارة");
                nm.createNotificationChannel(ch);
            }
        }
        if(android.os.Build.VERSION.SDK_INT>=33 && checkSelfPermission("android.permission.POST_NOTIFICATIONS")!=PackageManager.PERMISSION_GRANTED){
            requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"},210);
        }
    }

    void postAdminLocalNotification(String title,String body){
        if(android.os.Build.VERSION.SDK_INT>=33 && checkSelfPermission("android.permission.POST_NOTIFICATIONS")!=PackageManager.PERMISSION_GRANTED)return;
        android.app.Notification.Builder b;
        if(android.os.Build.VERSION.SDK_INT>=26)b=new android.app.Notification.Builder(this,"admin_review");
        else b=new android.app.Notification.Builder(this);
        b.setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle(title).setContentText(body).setAutoCancel(true);
        android.content.Intent i=new android.content.Intent(this,MainActivity.class);
        android.app.PendingIntent pi=android.app.PendingIntent.getActivity(this,210,i,android.os.Build.VERSION.SDK_INT>=23?android.app.PendingIntent.FLAG_UPDATE_CURRENT|android.app.PendingIntent.FLAG_IMMUTABLE:android.app.PendingIntent.FLAG_UPDATE_CURRENT);
        b.setContentIntent(pi);
        android.app.NotificationManager nm=(android.app.NotificationManager)getSystemService(NOTIFICATION_SERVICE);
        if(nm!=null)nm.notify((int)(System.currentTimeMillis()%100000),b.build());
    }

    void pendingCount(String collection,String field,String value,String key,String label,TextView button){
        if(db==null)return;
        db.collection(collection).whereEqualTo(field,value).get().addOnSuccessListener(snap->{
            int count=snap.size();
            String base=button.getText().toString().replaceAll("\\s*•\\s*\\d+$","");
            button.setText(count>0?base+" • "+count:base);
            int old=adminPrefs().getInt("pending_"+key,0);
            if(adminMode && count>old)postAdminLocalNotification("نجم ديرب — "+label,"يوجد "+count+" عنصر يحتاج مراجعة.");
            adminPrefs().edit().putInt("pending_"+key,count).apply();
        });
    }

    void refreshAdminBadges(){
        if(!isMainAdmin())return;
        pendingCount("changeRequests","status","pending","requests","طلبات",findViewById(R.id.btnAdminRequests));
        pendingCount("offers","status","pending","offers","عروض",findViewById(R.id.btnAdminOffers));
        pendingCount("ratings","status","pending","ratings","تقييمات",findViewById(R.id.btnAdminRatings));
        pendingCount("complaints","status","open","complaints","شكاوى",findViewById(R.id.btnAdminComplaints));
        pendingCount("businesses","status","pending","businesses","منشآت",findViewById(R.id.btnAdminBusinesses));
    }

'''
if marker not in s: raise SystemExit("dp marker not found")
s=s.replace(marker,helpers+marker,1)

# Add notification setup when admin panel is entered.
s=s.replace('    void loadRoleData(){\n        if(isMainAdmin())loadAdminStats();',
            '    void loadRoleData(){\n        if(isMainAdmin()){initAdminNotifications();loadAdminStats();refreshAdminBadges();}')

# Correct admin return targets.
s=s.replace('findViewById(R.id.btnAdminAddBusiness).setOnClickListener(v->{if(isMainAdmin()){clearForm();show(addPanel);}else toast("هذه الصلاحية للمدير الرئيسي فقط.");});',
            'findViewById(R.id.btnAdminAddBusiness).setOnClickListener(v->{if(isMainAdmin()){adminReturnSection=R.id.businessSection;clearForm();show(addPanel);}else toast("هذه الصلاحية للمدير الرئيسي فقط.");});')
s=s.replace('findViewById(R.id.btnBackAdd).setOnClickListener(v->showHome());',
            'findViewById(R.id.btnBackAdd).setOnClickListener(v->{if(adminMode)returnToAdmin();else showHome();});')
s=s.replace('findViewById(R.id.btnBackOffers).setOnClickListener(v->showHome());',
            'findViewById(R.id.btnBackOffers).setOnClickListener(v->{if(adminMode)returnToAdmin();else showHome();});')
s=s.replace('findViewById(R.id.btnAdminAddOffer).setOnClickListener(v->openAdminOfferForm());',
            'findViewById(R.id.btnAdminAddOffer).setOnClickListener(v->{adminReturnSection=R.id.offerSection;openAdminOfferForm();});')
s=s.replace('edit.setOnClickListener(v->{editingBusinessId=d.getId();fillBusiness(d);show(addPanel);});',
            'edit.setOnClickListener(v->{adminReturnSection=R.id.businessSection;editingBusinessId=d.getId();fillBusiness(d);show(addPanel);});')

# Notify administration when customer/owner creates reviewable items.
s=s.replace('db.collection("ratings").document(rid).set(m).addOnSuccessListener(x->{createAdminNotification("rating",bid,"تقييم جديد","يوجد تقييم جديد يحتاج مراجعة.");toast("تم إرسال التقييم للمراجعة");});',
            'db.collection("ratings").document(rid).set(m).addOnSuccessListener(x->{createAdminNotification("rating",bid,"تقييم جديد","يوجد تقييم جديد يحتاج مراجعة.");toast("تم إرسال التقييم للمراجعة");});')
s=s.replace('db.collection("complaints").add(m).addOnSuccessListener(x->{serviceStatus.setText("✅ تم إرسال الرسالة لخدمة العملاء.");',
            'db.collection("complaints").add(m).addOnSuccessListener(x->{createAdminNotification("complaint","", "شكوى/اقتراح جديد","وصلت رسالة جديدة لخدمة العملاء وتحتاج متابعة.");serviceStatus.setText("✅ تم إرسال الرسالة لخدمة العملاء.");')
s=s.replace('}).addOnSuccessListener(x->{offerStatus.setText(admin?"✅ تم نشر العرض.":"✅ تم إرسال العرض للمراجعة.");',
            '}).addOnSuccessListener(x->{if(!admin)createAdminNotification("offer",bid,"عرض جديد","يوجد عرض جديد يحتاج مراجعة.");offerStatus.setText(admin?"✅ تم نشر العرض.":"✅ تم إرسال العرض للمراجعة.");')
s=s.replace('db.collection("changeRequests").add(req).addOnSuccessListener(x->addStatus.setText("✅ تم إرسال التعديل للإدارة. لن يظهر للعامة إلا بعد الموافقة.")).addOnFailureListener',
            'db.collection("changeRequests").add(req).addOnSuccessListener(x->{createAdminNotification("changeRequest",bid,"طلب تعديل جديد","صاحب المنشأة أرسل تعديلات تحتاج مراجعة.");addStatus.setText("✅ تم إرسال التعديل للإدارة. لن يظهر للعامة إلا بعد الموافقة.");}).addOnFailureListener')

# Refresh badge counts whenever the admin resumes or completes moderation.
s=s.replace('@Override protected void onResume(){super.onResume();}',
            '@Override protected void onResume(){super.onResume();if(adminMode)refreshAdminBadges();}')
s=s.replace('d.getReference().update("status","approved").addOnSuccessListener(x->{String bid=d.getString("businessId");recalcRating(bid);});',
            'd.getReference().update("status","approved").addOnSuccessListener(x->{String bid=d.getString("businessId");recalcRating(bid);refreshAdminBadges();});')

# Use the user's exact logo image; only resize/compress for Android packaging.
dst=ROOT/'app/src/main/res/drawable/ic_launcher_photo.jpg'
if ICON_SRC.exists():
    shutil.copy2(ICON_SRC,dst)
else:
    raise SystemExit("User icon asset not found: "+str(ICON_SRC))

# Remove the V28 generated icon resource and point the manifest at the user's image.
xml_icon=ROOT/'app/src/main/res/drawable/ic_launcher.xml'
if xml_icon.exists(): xml_icon.unlink()
manifest=MANIFEST.read_text(encoding='utf-8')
manifest=manifest.replace('@drawable/ic_launcher','@drawable/ic_launcher_photo')
MANIFEST.write_text(manifest,encoding='utf-8')

# Permission required for Android 13+ local admin notifications.
if 'android.permission.POST_NOTIFICATIONS' not in manifest:
    manifest=manifest.replace('<uses-permission android:name="android.permission.INTERNET" />',
                              '<uses-permission android:name="android.permission.INTERNET" />\n    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />')
MANIFEST.write_text(manifest,encoding='utf-8')

# Small visual cleanup for the admin buttons and card spacing.
lay=LAYOUT.read_text(encoding='utf-8')
lay=lay.replace('android:text="📊 الإحصائيات"', 'android:text="📊 الإحصائيات" android:textAllCaps="false"')
lay=lay.replace('android:text="🕐 الطلبات"', 'android:text="🕐 الطلبات" android:textAllCaps="false"')
lay=lay.replace('android:text="🎁 العروض"', 'android:text="🎁 العروض" android:textAllCaps="false"')
lay=lay.replace('android:text="⭐ التقييمات"', 'android:text="⭐ التقييمات" android:textAllCaps="false"')
lay=lay.replace('android:text="📣 الشكاوى"', 'android:text="📣 الشكاوى" android:textAllCaps="false"')
lay=lay.replace('android:text="🏪 المنشآت"', 'android:text="🏪 المنشآت" android:textAllCaps="false"')
LAYOUT.write_text(lay,encoding='utf-8')

print("V29 patch prepared")
