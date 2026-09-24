from pathlib import Path
p=Path("app/src/main/java/com/negmdiarb/app/MainActivity.java")
s=p.read_text(encoding="utf-8")

if "void installPublicContributionButtons()" not in s:
    extra_methods = r'''    void installPublicContributionButtons(){
        if(homeStatus==null || homeStatus.getParent()==null)return;
        ViewGroup parent=(ViewGroup)homeStatus.getParent();
        if(parent.findViewWithTag("publicContributionRow")!=null)return;
        LinearLayout row=new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER);
        row.setTag("publicContributionRow");
        Button suggest=btn("➕ اقترح إضافة منشأة");
        Button service=btn("💬 الشكاوى والاقتراحات");
        styleAction(suggest,row);
        styleAction(service,row);
        suggest.setOnClickListener(v->showBusinessSuggestionDialog());
        service.setOnClickListener(v->show(servicePanel));
        int idx=parent.indexOfChild(homeStatus);
        parent.addView(row,Math.min(idx+1,parent.getChildCount()),new LinearLayout.LayoutParams(-1,dp(56)));
    }

    void showBusinessSuggestionDialog(){
        LinearLayout l=new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setPadding(dp(18),dp(8),dp(18),dp(6));
        EditText nm=new EditText(this);nm.setHint("اسم المنشأة / المحل *");
        Spinner cat=new Spinner(this);
        cat.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"مطاعم","محلات","عيادات","صيدليات","خدمات","ملابس","إلكترونيات","مقاهي","مخابز","أخرى"}));
        EditText ad=new EditText(this);ad.setHint("العنوان");
        EditText ph=new EditText(this);ph.setHint("رقم الهاتف (اختياري)");ph.setInputType(3);
        EditText ds=new EditText(this);ds.setHint("وصف مختصر / الخدمات");ds.setMinLines(3);ds.setGravity(Gravity.TOP|Gravity.RIGHT);
        l.addView(nm);l.addView(cat);l.addView(ad);l.addView(ph);l.addView(ds);
        new AlertDialog.Builder(this)
            .setTitle("➕ اقتراح إضافة منشأة")
            .setMessage("سيصل الاقتراح للإدارة للمراجعة أولًا، ولن يظهر للمستخدمين إلا بعد اعتماد الإدارة.")
            .setView(l)
            .setPositiveButton("إرسال للإدارة",(d,w)->{
                FirebaseUser u=auth.getCurrentUser();
                if(u==null){toast("جارٍ تجهيز الاتصال، حاول مرة أخرى.");return;}
                String businessName=nm.getText().toString().trim();
                if(businessName.isEmpty()){toast("اكتب اسم المنشأة.");return;}
                Map<String,Object> m=new HashMap<>();
                m.put("name",businessName);
                m.put("category",cat.getSelectedItem().toString());
                m.put("address",ad.getText().toString().trim());
                m.put("phone",ph.getText().toString().trim());
                m.put("description",ds.getText().toString().trim());
                m.put("uid",u.getUid());
                m.put("status","pending");
                m.put("createdAt",FieldValue.serverTimestamp());
                db.collection("businessRequests").add(m).addOnSuccessListener(x->{
                    createAdminNotification("business",x.getId(),"","اقتراح منشأة جديدة","يوجد اقتراح منشأة جديد يحتاج مراجعة: "+businessName);
                    toast("✅ تم إرسال الاقتراح للإدارة.");
                }).addOnFailureListener(e->toast("تعذر إرسال الاقتراح: "+safe(e.getMessage())));
            })
            .setNegativeButton("إلغاء",null).show();
    }

    void loadBusinessSuggestions(){
        if(!isMainAdmin()||db==null)return;
        db.collection("businessRequests").whereEqualTo("status","pending").limit(100).get().addOnSuccessListener(ss->{
            if(ss.isEmpty()){addText(requestList,"لا توجد اقتراحات منشآت جديدة.");return;}
            TextView h=tv("📌 اقتراحات إضافة منشآت");
            h.setTextSize(18);h.setTypeface(null,android.graphics.Typeface.BOLD);requestList.addView(h);
            for(DocumentSnapshot d:ss){
                LinearLayout c=box();
                c.addView(tv("🏪 "+safe(d.getString("name"))+"\\nالتصنيف: "+safe(d.getString("category"))+"\\n📍 "+safe(d.getString("address"))+"\\n☎ "+safe(d.getString("phone"))+"\\n"+safe(d.getString("description"))));
                LinearLayout actions=new LinearLayout(this);actions.setOrientation(LinearLayout.HORIZONTAL);
                Button approve=btn("✅ اعتماد وإضافة"),reject=btn("❌ رفض");
                styleAction(approve,actions);styleAction(reject,actions);c.addView(actions);
                approve.setOnClickListener(v->approveBusinessSuggestion(d));
                reject.setOnClickListener(v->d.getReference().update("status","rejected").addOnSuccessListener(x->{toast("تم رفض الاقتراح.");loadRequests();loadBusinessSuggestions();refreshAdminBadges();}));
                requestList.addView(c);
            }
        });
    }

    void approveBusinessSuggestion(DocumentSnapshot d){
        if(!isMainAdmin())return;
        Map<String,Object> b=new HashMap<>();
        b.put("name",safe(d.getString("name")));
        b.put("category",safe(d.getString("category")));
        b.put("address",safe(d.getString("address")));
        b.put("phone",safe(d.getString("phone")));
        b.put("description",safe(d.getString("description")));
        b.put("active",true);b.put("status","approved");b.put("featured",false);
        b.put("ratingAvg",0.0);b.put("ratingCount",0L);b.put("createdAt",FieldValue.serverTimestamp());
        db.collection("businesses").add(b).addOnSuccessListener(x->
            d.getReference().update("status","approved","businessId",x.getId()).addOnSuccessListener(y->{
                toast("✅ تم اعتماد المنشأة وإضافتها.");
                loadRequests();loadBusinessSuggestions();refreshAdminBadges();
            })
        ).addOnFailureListener(e->toast("تعذر إضافة المنشأة: "+safe(e.getMessage())));
    }

'''
    marker="    void installBackHandler()"
    if marker not in s: raise SystemExit("marker installBackHandler not found")
    s=s.replace(marker,extra_methods+marker,1)

# Put the two public buttons in the home screen after the home-status view is bound.
if "installPublicContributionButtons();" not in s:
    s=s.replace("    void setup(){" ,"    void setup(){\\n        installPublicContributionButtons();",1)

# Let the existing admin requests section also show public business suggestions.
s=s.replace(
'findViewById(R.id.btnAdminRequests).setOnClickListener(v->{openAdminSection(R.id.requestSection);loadRequests();});',
'findViewById(R.id.btnAdminRequests).setOnClickListener(v->{openAdminSection(R.id.requestSection);loadRequests();loadBusinessSuggestions();});'
)

p.write_text(s,encoding="utf-8")
print("EXTRA PUBLIC CONTRIBUTIONS PATCH OK")
