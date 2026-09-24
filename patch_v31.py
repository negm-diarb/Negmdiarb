from pathlib import Path
p=Path("app/src/main/java/com/negmdiarb/app/MainActivity.java")
s=p.read_text(encoding="utf-8")

def method_replace(src,name,repl):
    sig="    void "+name+"("
    a=src.find(sig)
    if a<0: raise SystemExit("method not found: "+name)
    b=src.find("{",a); depth=0
    for i in range(b,len(src)):
        if src[i]=="{": depth+=1
        elif src[i]=="}":
            depth-=1
            if depth==0: return src[:a]+repl+"\n"+src[i+1:]
    raise SystemExit("unbalanced "+name)

# Navigation state: explicit source screen, never infer from adminMode.
if "boolean returnToAdminAfterForm=false;" not in s:
    marker='public class MainActivity extends AppCompatActivity {'
    if marker in s:
        s=s.replace(marker, marker+'\n    boolean returnToAdminAfterForm=false;', 1)
    else:
        marker2='public class MainActivity extends Activity {'
        if marker2 in s:
            s=s.replace(marker2, marker2+'\n    boolean returnToAdminAfterForm=false;', 1)
        else:
            raise SystemExit("MainActivity class marker not found")

s=s.replace('findViewById(R.id.btnAdminAddBusiness).setOnClickListener(v->{if(isMainAdmin()){clearForm();show(addPanel);}', 'findViewById(R.id.btnAdminAddBusiness).setOnClickListener(v->{if(isMainAdmin()){returnToAdminAfterForm=true;clearForm();show(addPanel);}')
s=s.replace('findViewById(R.id.btnAdminAddOffer).setOnClickListener(v->openAdminOfferForm());', 'findViewById(R.id.btnAdminAddOffer).setOnClickListener(v->{returnToAdminAfterForm=true;openAdminOfferForm();});')
s=s.replace('findViewById(R.id.btnBackAdd).setOnClickListener(v->showHome());', 'findViewById(R.id.btnBackAdd).setOnClickListener(v->{if(returnToAdminAfterForm){returnToAdminAfterForm=false;show(adminPanel);openAdminSection(R.id.businessSection);}else showHome();});')
s=s.replace('findViewById(R.id.btnBackOffers).setOnClickListener(v->showHome());', 'findViewById(R.id.btnBackOffers).setOnClickListener(v->{if(returnToAdminAfterForm){returnToAdminAfterForm=false;show(adminPanel);openAdminSection(R.id.offerSection);}else showHome();});')

# Hardware back uses the same explicit state.
method_replace(s,"installBackHandler",'''    void installBackHandler(){
        getOnBackPressedDispatcher().addCallback(this,new OnBackPressedCallback(true){
            @Override public void handleOnBackPressed(){
                if(addPanel.getVisibility()==View.VISIBLE){
                    if(returnToAdminAfterForm){returnToAdminAfterForm=false;show(adminPanel);openAdminSection(R.id.businessSection);}
                    else showHome();
                    return;
                }
                if(offersPanel.getVisibility()==View.VISIBLE){
                    if(returnToAdminAfterForm){returnToAdminAfterForm=false;show(adminPanel);openAdminSection(R.id.offerSection);}
                    else showHome();
                    return;
                }
                if(adminPanel.getVisibility()==View.VISIBLE){
                    new AlertDialog.Builder(MainActivity.this).setTitle("العودة من لوحة المدير")
                        .setMessage("هل تريد العودة للرئيسية؟").setNegativeButton("إلغاء",null)
                        .setPositiveButton("الرئيسية",(d,w)->showHome()).show();
                    return;
                }
                if(homePanel.getVisibility()==View.VISIBLE){
                    new AlertDialog.Builder(MainActivity.this).setTitle("الخروج من نجم ديرب")
                        .setMessage("هل تريد الخروج من التطبيق؟").setNegativeButton("إلغاء",null)
                        .setPositiveButton("خروج",(d,w)->finish()).show();
                }else showHome();
            }
        });
    }''')

# Professional two-row card.
method_replace(s,"addBusinessCard",'''    void addBusinessCard(DocumentSnapshot d){
        LinearLayout card=box(); card.setElevation(dp(3));
        String n=safe(d.getString("name")); double avg=num(d,"ratingAvg");
        long cnt=d.getLong("ratingCount")==null?0:d.getLong("ratingCount");
        TextView title=tv((truth(d,"featured")?"★ ":"")+n); title.setTextSize(19); title.setTypeface(null,android.graphics.Typeface.BOLD); title.setTextColor(Color.rgb(16,42,102)); card.addView(title);
        TextView cat=tv(safe(d.getString("category"))); cat.setTextSize(13); cat.setTextColor(Color.rgb(104,115,134)); card.addView(cat);
        card.addView(buildStarsRow(avg,cnt,false));
        String desc=safe(d.getString("description")); if(desc.length()>100)desc=desc.substring(0,100)+"…";
        TextView loc=tv("📍 "+safe(d.getString("address"))+(desc.isEmpty()?"":"\n"+desc)); loc.setTextSize(14); loc.setTextColor(Color.rgb(53,64,83)); card.addView(loc);
        LinearLayout r1=new LinearLayout(this); r1.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout r2=new LinearLayout(this); r2.setOrientation(LinearLayout.HORIZONTAL);
        Button mapBtn=btn("خريطة"),callBtn=btn("اتصال"),waBtn=btn("واتساب"),rateBtn=btn("تقييم"),favBtn=btn(favoriteIds.contains(d.getId())?"♥ حفظ":"♡ حفظ"),shareBtn=btn("مشاركة");
        Button[] row1={mapBtn,callBtn,waBtn},row2={rateBtn,favBtn,shareBtn};
        for(Button b:row1)styleAction(b,r1);
        for(Button b:row2)styleAction(b,r2);
        card.addView(r1);card.addView(r2);
        card.setOnClickListener(v->{logEvent("businessViews",d.getId());showBusinessDetails(d);});
        mapBtn.setOnClickListener(v->{logEvent("mapClicks",d.getId());openMap(d);});
        callBtn.setOnClickListener(v->{logEvent("callClicks",d.getId());call(d.getString("phone"));});
        waBtn.setOnClickListener(v->{logEvent("whatsappClicks",d.getId());wa(d.getId(),d.getString("whatsapp"));});
        rateBtn.setOnClickListener(v->showRatingDialog(d.getId()));
        favBtn.setOnClickListener(v->toggleFavorite(d.getId(),favBtn));
        shareBtn.setOnClickListener(v->shareBusiness(d));
        businessList.addView(card);
    }
    void styleAction(Button b,LinearLayout row){
        b.setAllCaps(false);b.setTextSize(12);b.setMinWidth(0);b.setMinHeight(0);b.setSingleLine(true);b.setGravity(Gravity.CENTER);b.setPadding(dp(2),0,dp(2),0);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(44),1);lp.setMargins(dp(2),dp(2),dp(2),dp(2));row.addView(b,lp);
    }''')

# Rating stores business name and creates a central admin review item.
method_replace(s,"showRatingDialog",'''    void showRatingDialog(String bid){
        LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(dp(18),dp(8),dp(18),dp(6));
        TextView hint=tv("اختار عدد النجوم");hint.setTextSize(15);hint.setTypeface(null,android.graphics.Typeface.BOLD);hint.setGravity(Gravity.CENTER);l.addView(hint);
        LinearLayout stars=new LinearLayout(this);stars.setOrientation(LinearLayout.HORIZONTAL);stars.setGravity(Gravity.CENTER);stars.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);l.addView(stars,new LinearLayout.LayoutParams(-1,dp(62)));
        final int[] selected={0};final TextView[] starViews=new TextView[5];
        for(int i=0;i<5;i++){final int value=i+1;TextView st=new TextView(this);starViews[i]=st;st.setText("☆");st.setTextSize(40);st.setGravity(Gravity.CENTER);st.setTextColor(Color.rgb(190,196,206));st.setOnClickListener(v->{selected[0]=value;for(int j=0;j<5;j++){starViews[j].setText(j<value?"★":"☆");starViews[j].setTextColor(j<value?Color.rgb(245,184,46):Color.rgb(190,196,206));}hint.setText(value+" من 5 نجوم");});stars.addView(st,new LinearLayout.LayoutParams(dp(56),dp(60)));}
        EditText tx=new EditText(this);tx.setHint("اكتب رأيك (اختياري)");tx.setMinLines(3);tx.setGravity(Gravity.TOP|Gravity.RIGHT);tx.setBackgroundResource(R.drawable.bg_search);l.addView(tx);
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle("تقييم المنشأة").setView(l).setPositiveButton("إرسال",null).setNegativeButton("إلغاء",null).create();
        dialog.setOnShowListener(x->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{
            if(selected[0]==0){hint.setText("اختر النجوم أولًا ⭐");return;}
            FirebaseUser u=auth.getCurrentUser();if(u==null){toast("سجّل الدخول أولًا.");return;}
            db.collection("businesses").document(bid).get().addOnSuccessListener(biz->{
                String businessName=safe(biz.getString("name"));
                String rid=u.getUid()+"_"+bid;Map<String,Object>m=new HashMap<>();
                m.put("businessId",bid);m.put("businessName",businessName);m.put("stars",selected[0]);m.put("text",tx.getText().toString().trim());m.put("status","pending");m.put("uid",u.getUid());m.put("createdAt",FieldValue.serverTimestamp());
                db.collection("ratings").document(rid).set(m).addOnSuccessListener(q->{
                    createAdminNotification("rating",rid,bid,"تقييم جديد","تقييم جديد يحتاج مراجعة"+(businessName.isEmpty()?"":" — "+businessName));
                    toast("✅ تم إرسال تقييمك للمراجعة");dialog.dismiss();
                }).addOnFailureListener(e->toast("تعذر إرسال التقييم: "+safe(e.getMessage())));
            }).addOnFailureListener(e->toast("تعذر قراءة بيانات المنشأة."));
        });dialog.show();
    }''')

# Central notification writer + listener. Local notification is only possible while the admin app is running.
helpers = '''    com.google.firebase.firestore.ListenerRegistration adminNotificationListener;
    boolean adminNotificationBaselineReady=false;
    void createAdminNotification(String type,String itemId,String businessId,String title,String body){
        if(db==null)return;
        Map<String,Object> n=new HashMap<>();n.put("type",type);n.put("itemId",itemId==null?"":itemId);n.put("businessId",businessId==null?"":businessId);n.put("title",title);n.put("body",body);n.put("status","pending");n.put("createdAt",FieldValue.serverTimestamp());
        db.collection("adminNotifications").add(n);
    }
    void startAdminNotificationListener(){
        if(!isMainAdmin()||db==null)return;
        if(adminNotificationListener!=null)adminNotificationListener.remove();
        adminNotificationBaselineReady=false;
        adminNotificationListener=db.collection("adminNotifications").whereEqualTo("status","pending").addSnapshotListener((snap,e)->{
            if(e!=null||snap==null)return;
            if(!adminNotificationBaselineReady){adminNotificationBaselineReady=true;refreshAdminBadges();return;}
            for(DocumentChange ch:snap.getDocumentChanges())if(ch.getType()==DocumentChange.Type.ADDED){
                DocumentSnapshot d=ch.getDocument();postAdminLocalNotification(safe(d.getString("title")),safe(d.getString("body")));
            }
            refreshAdminBadges();
        });
    }
    void postAdminLocalNotification(String title,String body){
        if(android.os.Build.VERSION.SDK_INT>=33 && checkSelfPermission("android.permission.POST_NOTIFICATIONS")!=PackageManager.PERMISSION_GRANTED)return;
        android.app.Notification.Builder b=android.os.Build.VERSION.SDK_INT>=26?new android.app.Notification.Builder(this,"admin_review"):new android.app.Notification.Builder(this);
        b.setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle(title).setContentText(body).setAutoCancel(true);
        android.app.NotificationManager nm=(android.app.NotificationManager)getSystemService(NOTIFICATION_SERVICE);if(nm!=null)nm.notify((int)(System.currentTimeMillis()%100000),b.build());
    }
    void refreshAdminBadges(){
        if(!isMainAdmin()||db==null)return;
        db.collection("adminNotifications").whereEqualTo("status","pending").get().addOnSuccessListener(s->{
            int n=s.size(); TextView[] vs={findViewById(R.id.btnAdminRequests),findViewById(R.id.btnAdminOffers),findViewById(R.id.btnAdminComplaints),findViewById(R.id.btnAdminRatings)};
            String[] labels={"طلبات","عروض","شكاوى","تقييمات"};String[] types={"changeRequest","offer","complaint","rating"};
            for(int i=0;i<vs.length;i++)if(vs[i]!=null){int count=0;for(DocumentSnapshot d:s)if(types[i].equals(safe(d.getString("type"))))count++;vs[i].setText(labels[i]+(count>0?" • "+count:""));}
            if(findViewById(R.id.btnAdminBusinesses)!=null){int c=0;for(DocumentSnapshot d:s)if("business".equals(safe(d.getString("type"))))c++;findViewById(R.id.btnAdminBusinesses).setContentDescription("منشآت"+(c>0?" • "+c:""));}
        });
    }
'''
if "void createAdminNotification(String type,String itemId" not in s:
    init_method = '''    void initAdminNotifications(){
        if(android.os.Build.VERSION.SDK_INT>=26){
            android.app.NotificationManager nm=(android.app.NotificationManager)getSystemService(NOTIFICATION_SERVICE);
            if(nm!=null)nm.createNotificationChannel(new android.app.NotificationChannel("admin_review","مراجعات الإدارة",android.app.NotificationManager.IMPORTANCE_HIGH));
        }
        if(android.os.Build.VERSION.SDK_INT>=33 && checkSelfPermission("android.permission.POST_NOTIFICATIONS")!=PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"},9001);
    }'''
    s=s.rstrip(); s=s[:-1]+helpers+init_method+"\n}"

# Hook owner change requests.
s=s.replace('db.collection("changeRequests").add(req).addOnSuccessListener(x->addStatus.setText("✅ تم إرسال التعديل للإدارة.', 'db.collection("changeRequests").add(req).addOnSuccessListener(x->{createAdminNotification("changeRequest",x.getId(),bid,"طلب تعديل منشأة","يوجد طلب تعديل يحتاج مراجعة.");addStatus.setText("✅ تم إرسال التعديل للإدارة.')

# Hook offer creation without depending on method name.
s=s.replace('db.collection("offers").add(m).addOnSuccessListener(x->{offerStatus.setText(admin?"✅ تم نشر العرض.":"✅ تم إرسال العرض للمراجعة.");', 'db.collection("offers").add(m).addOnSuccessListener(x->{if(!admin)createAdminNotification("offer",x.getId(),bid,"عرض جديد","يوجد عرض جديد يحتاج مراجعة.");offerStatus.setText(admin?"✅ تم نشر العرض.":"✅ تم إرسال العرض للمراجعة.");')

# Repair the owner change-request callback as one complete expression.\nbad='db.collection("changeRequests").add(req).addOnSuccessListener(x->{createAdminNotification("changeRequest",x.getId(),bid,"طلب تعديل منشأة","يوجد طلب تعديل يحتاج مراجعة.");addStatus.setText("✅ تم إرسال التعديل للإدارة. لن يظهر للعامة إلا بعد الموافقة.")).addOnFailureListener(e->addStatus.setText("❌ تعذر إرسال الطلب: "+safe(e.getMessage())));});'\ngood='db.collection("changeRequests").add(req).addOnSuccessListener(x->{createAdminNotification("changeRequest",x.getId(),bid,"طلب تعديل منشأة","يوجد طلب تعديل يحتاج مراجعة.");addStatus.setText("✅ تم إرسال التعديل للإدارة. لن يظهر للعامة إلا بعد الموافقة.");}).addOnFailureListener(e->addStatus.setText("❌ تعذر إرسال الطلب: "+safe(e.getMessage())));});'\ns=s.replace(bad,good)\n\n# Complaint notification hook deferred until the complaint method is replaced safely.\n# Start listener when admin session is established.
s=s.replace('loadRoleData();', 'loadRoleData();if(isMainAdmin()){initAdminNotifications();startAdminNotificationListener();refreshAdminBadges();}', 2)

# Final line-level repair: the owner change-request callback must close the lambda before addOnFailureListener.\nlines=[]\nfor line in s.splitlines():\n    if 'db.collection("changeRequests").add(req).addOnSuccessListener' in line:\n        line=line.replace('")).addOnFailureListener','");}).addOnFailureListener',1)\n    lines.append(line)\ns="\\n".join(lines)+"\\n"\n\np.write_text(s,encoding="utf-8")
print("V31 patch ready")
