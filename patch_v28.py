from pathlib import Path
import re

ROOT=Path('.')
JAVA=ROOT/'app/src/main/java/com/negmdiarb/app/MainActivity.java'
LAYOUT=ROOT/'app/src/main/res/layout/activity_main.xml'

def replace_method(src, start_sig, end_sig, repl):
    a=src.index(start_sig)
    b=src.index(end_sig,a)
    return src[:a]+repl+src[b:]

s=JAVA.read_text(encoding='utf-8')

s=replace_method(s,'    void addBusinessCard(DocumentSnapshot d){','    void toggleFavorite','''    void addBusinessCard(DocumentSnapshot d){
        LinearLayout card=box(); card.setElevation(dp(3));
        String n=safe(d.getString("name")); double avg=num(d,"ratingAvg");
        long cnt=d.getLong("ratingCount")==null?0:d.getLong("ratingCount");
        TextView title=tv((truth(d,"featured")?"★ ":"")+n); title.setTextSize(19); title.setTypeface(null,android.graphics.Typeface.BOLD); title.setTextColor(Color.rgb(16,42,102)); card.addView(title);
        TextView cat=tv(safe(d.getString("category"))); cat.setTextSize(13); cat.setTextColor(Color.rgb(104,115,134)); card.addView(cat);
        card.addView(buildStarsRow(avg,cnt,false));
        String desc=safe(d.getString("description")); if(desc.length()>100)desc=desc.substring(0,100)+"…";
        TextView loc=tv("📍 "+safe(d.getString("address"))+(desc.isEmpty()?"":"\n"+desc)); loc.setTextSize(14); loc.setTextColor(Color.rgb(53,64,83)); card.addView(loc);
        LinearLayout a=new LinearLayout(this); a.setOrientation(LinearLayout.HORIZONTAL); a.setGravity(Gravity.CENTER_VERTICAL);
        Button mapBtn=btn("خريطة"),callBtn=btn("اتصال"),waBtn=btn("واتساب"),rateBtn=btn("تقييم"),favBtn=btn(favoriteIds.contains(d.getId())?"♥":"♡"),shareBtn=btn("مشاركة");
        rateBtn.setTextSize(14); rateBtn.setBackgroundResource(R.drawable.bg_gold); rateBtn.setTextColor(Color.rgb(92,65,0));
        Button[] buttons={mapBtn,callBtn,waBtn,rateBtn,favBtn,shareBtn}; for(Button b:buttons)a.addView(b,new LinearLayout.LayoutParams(0,dp(46),1)); card.addView(a);
        card.setOnClickListener(v->{logEvent("businessViews",d.getId());showBusinessDetails(d);});
        mapBtn.setOnClickListener(v->{logEvent("mapClicks",d.getId());openMap(d);}); callBtn.setOnClickListener(v->{logEvent("callClicks",d.getId());call(d.getString("phone"));}); waBtn.setOnClickListener(v->{logEvent("whatsappClicks",d.getId());wa(d.getId(),d.getString("whatsapp"));}); rateBtn.setOnClickListener(v->showRatingDialog(d.getId())); favBtn.setOnClickListener(v->toggleFavorite(d.getId(),favBtn)); shareBtn.setOnClickListener(v->shareBusiness(d)); businessList.addView(card);
    }

    LinearLayout buildStarsRow(double avg,long cnt,boolean large){
        LinearLayout row=new LinearLayout(this); row.setOrientation(LinearLayout.HORIZONTAL); row.setGravity(Gravity.CENTER_VERTICAL); row.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);
        int size=large?32:22, rounded=(int)Math.round(avg);
        for(int i=1;i<=5;i++){ TextView st=new TextView(this); st.setText(i<=rounded?"★":"☆"); st.setTextSize(size); st.setGravity(Gravity.CENTER); st.setTextColor(i<=rounded?Color.rgb(245,184,46):Color.rgb(190,196,206)); row.addView(st,new LinearLayout.LayoutParams(dp(size+7),dp(size+10))); }
        TextView txt=tv(avg<=0?"جديد — كن أول من يقيّم هذه المنشأة":String.format(Locale.US,"%.1f  •  %d تقييم",avg,cnt)); txt.setTextSize(large?15:13); txt.setTypeface(null,android.graphics.Typeface.BOLD); txt.setTextColor(Color.rgb(92,65,0)); row.addView(txt); return row;
    }

''')

s=replace_method(s,'    void showRatingDialog(String bid){','    void sendComplaint','''    void showRatingDialog(String bid){
        LinearLayout l=new LinearLayout(this); l.setOrientation(LinearLayout.VERTICAL); l.setPadding(dp(18),dp(8),dp(18),dp(6));
        TextView hint=tv("اختار عدد النجوم"); hint.setTextSize(15); hint.setTypeface(null,android.graphics.Typeface.BOLD); hint.setGravity(Gravity.CENTER); l.addView(hint);
        LinearLayout stars=new LinearLayout(this); stars.setOrientation(LinearLayout.HORIZONTAL); stars.setGravity(Gravity.CENTER); stars.setLayoutDirection(View.LAYOUT_DIRECTION_LTR); l.addView(stars,new LinearLayout.LayoutParams(-1,dp(62)));
        final int[] selected={0}; final TextView[] starViews=new TextView[5];
        for(int i=0;i<5;i++){ final int value=i+1; TextView st=new TextView(this); starViews[i]=st; st.setText("☆"); st.setTextSize(40); st.setGravity(Gravity.CENTER); st.setTextColor(Color.rgb(190,196,206)); st.setOnClickListener(v->{selected[0]=value; for(int j=0;j<5;j++){starViews[j].setText(j<value?"★":"☆"); starViews[j].setTextColor(j<value?Color.rgb(245,184,46):Color.rgb(190,196,206));} hint.setText(value+" من 5 نجوم");}); stars.addView(st,new LinearLayout.LayoutParams(dp(56),dp(60))); }
        EditText tx=new EditText(this); tx.setHint("اكتب رأيك (اختياري)"); tx.setMinLines(3); tx.setGravity(Gravity.TOP|Gravity.RIGHT); tx.setBackgroundResource(R.drawable.bg_search); l.addView(tx);
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle("تقييم المنشأة").setView(l).setPositiveButton("إرسال",null).setNegativeButton("إلغاء",null).create();
        dialog.setOnShowListener(x->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{
            if(selected[0]==0){hint.setText("اختر النجوم أولًا ⭐");return;} FirebaseUser u=auth.getCurrentUser(); if(u==null){toast("سجّل الدخول أولًا.");return;}
            String rid=u.getUid()+"_"+bid; Map<String,Object>m=new HashMap<>(); m.put("businessId",bid); m.put("stars",selected[0]); m.put("text",tx.getText().toString().trim()); m.put("status","pending"); m.put("uid",u.getUid()); m.put("createdAt",FieldValue.serverTimestamp());
            db.collection("ratings").document(rid).set(m).addOnSuccessListener(q->{toast("✅ تم إرسال تقييمك للمراجعة");dialog.dismiss();}).addOnFailureListener(e->hint.setText("تعذر إرسال التقييم. جرّب مرة أخرى."));
        })); dialog.show();
    }

''')
s=s.replace('        l.addView(tv("⭐ "+(avg==0?"جديد":String.format(Locale.US,"%.1f من %d تقييم",avg,cnt))));','        l.addView(buildStarsRow(avg,cnt,true));')

s=replace_method(s,'    void createOwnerAccount(){','    interface UserMapBuilder','''    void createOwnerAccount(){
        if(!isMainAdmin()){toast("المدير الرئيسي فقط.");return;}
        db.collection("businesses").whereEqualTo("status","approved").limit(300).get().addOnSuccessListener(bs->{
            ArrayList<DocumentSnapshot> list=new ArrayList<>(); for(DocumentSnapshot b:bs)list.add(b); if(list.isEmpty()){toast("أضف منشأة أولًا ثم أنشئ حساب صاحبها.");return;}
            LinearLayout l=new LinearLayout(this); l.setOrientation(LinearLayout.VERTICAL); l.setPadding(dp(20),dp(10),dp(20),dp(10));
            EditText nm=new EditText(this);nm.setHint("اسم صاحب المنشأة"); EditText em=new EditText(this);em.setHint("البريد الإلكتروني"); EditText ph=new EditText(this);ph.setHint("رقم الهاتف"); EditText pw=new EditText(this);pw.setHint("كلمة المرور (6+ أحرف)");pw.setInputType(0x81);
            Spinner sp=new Spinner(this); String[] names=new String[list.size()]; for(int i=0;i<list.size();i++){DocumentSnapshot b=list.get(i);String owner=safe(b.getString("ownerUid"));names[i]=safe(b.getString("name"))+(!owner.isEmpty()?"  •  مرتبطة":"  •  متاحة");} sp.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,names));
            l.addView(nm);l.addView(em);l.addView(ph);l.addView(pw);l.addView(sp);
            AlertDialog dialog=new AlertDialog.Builder(this).setTitle("👤 إنشاء حساب صاحب منشأة").setView(l).setPositiveButton("إنشاء",null).setNegativeButton("إلغاء",null).create();
            dialog.setOnShowListener(z->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{
                String ownerName=nm.getText().toString().trim(),email=em.getText().toString().trim(),pass=pw.getText().toString(); if(ownerName.isEmpty()||email.isEmpty()||pass.length()<6){toast("أكمل البيانات وكلمة المرور 6 أحرف على الأقل.");return;}
                DocumentSnapshot b=list.get(sp.getSelectedItemPosition()); String bid=b.getId(); if(!safe(b.getString("ownerUid")).isEmpty()){toast("⛔ هذه المنشأة مرتبطة بالفعل بحساب صاحب منشأة.");return;}
                db.collection("users").whereEqualTo("role","owner").whereEqualTo("businessId",bid).limit(1).get().addOnSuccessListener(existing->{ if(!existing.isEmpty()){toast("⛔ يوجد حساب صاحب منشأة مرتبط بهذه المنشأة بالفعل.");return;}
                    createAuthUser(email,pass,m->{m.put("role","owner");m.put("displayName",ownerName);m.put("email",email);m.put("phone",ph.getText().toString().trim());m.put("businessName",safe(b.getString("name")));m.put("businessId",bid);m.put("enabled",true);m.put("permissions",Arrays.asList("owner_profile_edit_request","owner_offer_create","owner_requests_view"));m.put("createdAt",FieldValue.serverTimestamp());},"تم إنشاء حساب صاحب المنشأة وربطه."); dialog.dismiss();
                }).addOnFailureListener(e->toast("تعذر التحقق من الحساب المرتبط: "+safe(e.getMessage())));
            })); dialog.show();
        }).addOnFailureListener(e->toast("تعذر تحميل المنشآت: "+safe(e.getMessage())));
    }

''')
s=s.replace('if(msg.contains("PERMISSION_DENIED")||msg.contains("PERMISSION_DENIED"))msg="صلاحيات Firestore رفضت إنشاء الحساب أو ربط المنشأة. انشر قواعد V27 الجديدة ثم جرّب مرة أخرى.";', 'if(msg.contains("PERMISSION_DENIED"))msg="صلاحيات Firestore رفضت إنشاء الحساب أو ربط المنشأة. يجب نشر قواعد V28 مرة واحدة في Firebase Console ثم إعادة المحاولة.";')

s=s.replace('LinearLayout box(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(14,14,14,14);l.setBackgroundResource(R.drawable.bg_card);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.setMargins(0,0,0,10);l.setLayoutParams(p);return l;}', 'LinearLayout box(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(dp(15),dp(15),dp(15),dp(15));l.setBackgroundResource(R.drawable.bg_card);l.setElevation(dp(2));LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.setMargins(0,0,0,dp(12));l.setLayoutParams(p);return l;}')
s=s.replace('TextView tv(String s){TextView t=new TextView(this);t.setText(s);t.setTextSize(16);t.setTextColor(android.graphics.Color.rgb(23,32,51));t.setPadding(6,6,6,6);return t;}', 'TextView tv(String s){TextView t=new TextView(this);t.setText(s);t.setTextSize(16);t.setTextColor(android.graphics.Color.rgb(23,32,51));t.setPadding(dp(6),dp(6),dp(6),dp(6));return t;}')
s=s.replace('Button btn(String s){Button b=new Button(this);b.setText(s);b.setTextSize(13);b.setMinHeight(0);b.setPadding(4,0,4,0);b.setBackgroundResource(R.drawable.bg_card);return b;}', 'Button btn(String s){Button b=new Button(this);b.setText(s);b.setTextSize(13);b.setMinHeight(0);b.setAllCaps(false);b.setPadding(dp(4),0,dp(4),0);b.setBackgroundResource(R.drawable.bg_card);b.setTextColor(Color.rgb(23,32,51));b.setStateListAnimator(null);return b;}')
JAVA.write_text(s,encoding='utf-8')

(ROOT/'app/src/main/res/drawable/bg_hero.xml').write_text('<shape xmlns:android="http://schemas.android.com/apk/res/android"><gradient android:startColor="#081A3D" android:centerColor="#173B8F" android:endColor="#3B62B6" android:angle="45"/><corners android:radius="26dp"/><stroke android:width="1dp" android:color="#F5B82E"/><padding android:left="22dp" android:top="20dp" android:right="22dp" android:bottom="20dp"/></shape>',encoding='utf-8')
(ROOT/'app/src/main/res/drawable/bg_card.xml').write_text('<shape xmlns:android="http://schemas.android.com/apk/res/android"><solid android:color="#FFFFFF"/><corners android:radius="20dp"/><stroke android:width="1dp" android:color="#DCE4F0"/><padding android:left="14dp" android:top="12dp" android:right="14dp" android:bottom="12dp"/></shape>',encoding='utf-8')
(ROOT/'app/src/main/res/drawable/bg_gold.xml').write_text('<shape xmlns:android="http://schemas.android.com/apk/res/android"><gradient android:startColor="#FFF9E8" android:endColor="#FFE9A8" android:angle="90"/><corners android:radius="15dp"/><stroke android:width="1dp" android:color="#E9AA24"/><padding android:left="8dp" android:top="4dp" android:right="8dp" android:bottom="4dp"/></shape>',encoding='utf-8')
(ROOT/'app/src/main/res/values/colors.xml').write_text('''<resources>
    <color name="brand_blue">#173B8F</color>
    <color name="brand_blue_dark">#081A3D</color>
    <color name="brand_gold">#F5B82E</color>
    <color name="surface">#FFFFFF</color>
    <color name="surface_alt">#F2F5FA</color>
    <color name="text_main">#172033</color>
    <color name="text_muted">#687386</color>
    <color name="success">#16835B</color>
</resources>
''',encoding='utf-8')

icon=ROOT/'app/src/main/res/drawable/ic_launcher.png'
if icon.exists(): icon.unlink()
(ROOT/'app/src/main/res/drawable/ic_launcher.xml').write_text('''<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item>
        <shape>
            <gradient android:startColor="#081A3D" android:centerColor="#173B8F" android:endColor="#0B2250" android:angle="45"/>
            <corners android:radius="90dp"/>
            <stroke android:width="7dp" android:color="#F5B82E"/>
        </shape>
    </item>
    <item android:left="95dp" android:top="95dp" android:right="95dp" android:bottom="95dp">
        <vector android:width="100dp" android:height="100dp" android:viewportWidth="1024" android:viewportHeight="1024">
            <path android:fillColor="#F6BB34" android:strokeColor="#FFDD82" android:strokeWidth="12" android:strokeLineJoin="round" android:pathData="M512,86 L609,378 L917,378 L668,561 L764,856 L512,680 L260,856 L356,561 L107,378 L415,378 Z"/>
            <path android:fillColor="#FFFFFF" android:pathData="M512,430 A64,64 0,1 1,512,558 A64,64 0,1 1,512,430"/>
        </vector>
    </item>
</layer-list>
''',encoding='utf-8')

ls=LAYOUT.read_text(encoding='utf-8')
ls=ls.replace('android:text="⭐ نجم ديرب" android:textColor="#FFFFFF" android:textSize="32sp"','android:text="نجم ديرب" android:textColor="#FFFFFF" android:textSize="34sp"')
ls=ls.replace('android:text="اكتشف أفضل الأماكن والخدمات حولك"','android:text="دليلك المحلي لاكتشاف الأماكن والخدمات"')
ls=ls.replace('android:text="كل اللي حواليك في مكان واحد"','android:text="بيانات مرتبة • تقييمات • عروض • خرائط"')
ls=ls.replace('android:text="🚀 لوحة التحكم الجديدة"','android:text="لوحة تحكم نجم ديرب"')
LAYOUT.write_text(ls,encoding='utf-8')

print('PATCH V28 OK')
