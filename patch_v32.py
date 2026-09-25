from pathlib import Path
import re

p=Path("app/src/main/java/com/negmdiarb/app/MainActivity.java")
s=p.read_text(encoding="utf-8")

def need(old,new,label):
    global s
    if old not in s:
        raise SystemExit("MISSING: "+label)
    s=s.replace(old,new,1)

# Keep the V30 UI and authentication untouched. Only repair the requested behaviors.

# 1) Admin add/edit screens must return to the admin panel, not home.
if "boolean adminReturnToPanel" not in s:
    s=s.replace("boolean adminMode=false;", "boolean adminMode=false; boolean adminReturnToPanel=false;", 1)

# Normalize whichever V30/V29 listener form exists.
if 'findViewById(R.id.btnAdminAddBusiness).setOnClickListener' not in s:
    raise SystemExit("MISSING: admin add business listener")
s=re.sub(
    r'findViewById\(R\.id\.btnAdminAddBusiness\)\.setOnClickListener\(v->\{if\(isMainAdmin\(\)\)\{clearForm\(\);show\(addPanel\);\}else toast\("[^"]*"\);\}\);',
    'findViewById(R.id.btnAdminAddBusiness).setOnClickListener(v->{if(isMainAdmin()){adminReturnToPanel=true;clearForm();show(addPanel);}else toast("هذه الصلاحية للمدير الرئيسي فقط.");});',
    s,count=1
)

if 'findViewById(R.id.btnBackAdd).setOnClickListener' not in s:
    raise SystemExit("MISSING: back add listener")
s=re.sub(
    r'findViewById\(R\.id\.btnBackAdd\)\.setOnClickListener\([^;]+;\);',
    'findViewById(R.id.btnBackAdd).setOnClickListener(v->{if(adminReturnToPanel || adminMode){adminReturnToPanel=false;returnToAdmin();}else showHome();});',
    s,count=1
)

# Hardware back must use the explicit flag.
if "if(addPanel.getVisibility()==View.VISIBLE)" in s:
    s=re.sub(
        r'if\(addPanel\.getVisibility\(\)==View\.VISIBLE\)\{[^}]*\}',
        'if(addPanel.getVisibility()==View.VISIBLE){if(adminReturnToPanel || adminMode){adminReturnToPanel=false;returnToAdmin();}else showHome();return;}',
        s,count=1
    )

# 2) Admin Add Offer enters the same return path.
if 'findViewById(R.id.btnAdminAddOffer).setOnClickListener' not in s:
    raise SystemExit("MISSING: admin add offer listener")
s=re.sub(
    r'findViewById\\(R\\.id\\.btnAdminAddOffer\\)\\.setOnClickListener\\([^;]+;\\);',
    'findViewById(R.id.btnAdminAddOffer).setOnClickListener(v->{adminReturnToPanel=true;openAdminOfferForm();});',
    s,count=1
)
s=s.replace(
'findViewById(R.id.btnBackOffers).setOnClickListener(v->showHome());',
'findViewById(R.id.btnBackOffers).setOnClickListener(v->{if(adminReturnToPanel){adminReturnToPanel=false;returnToAdmin();}else showHome();});',
1
)

# 3) Hardware back from add/offer also returns to admin when entered from admin.
if "if(addPanel.getVisibility()==View.VISIBLE)" in s:
    s=s.replace(
        'if(addPanel.getVisibility()==View.VISIBLE){if(adminMode){returnToAdmin();}else showHome();return;}',
        'if(addPanel.getVisibility()==View.VISIBLE){if(adminReturnToPanel){adminReturnToPanel=false;returnToAdmin();}else showHome();return;}',
        1
    )
    s=s.replace(
        'if(offersPanel.getVisibility()==View.VISIBLE){if(adminMode){returnToAdmin();}else showHome();return;}',
        'if(offersPanel.getVisibility()==View.VISIBLE){if(adminReturnToPanel){adminReturnToPanel=false;returnToAdmin();}else showHome();return;}',
        1
    )

# 4) Rating submission creates an admin review notification.
needle='db.collection("ratings").document(rid).set(m).addOnSuccessListener(q->{'
if needle not in s:
    raise SystemExit("MISSING: rating success listener")
if 'createAdminNotification("rating",rid' not in s:
    s=s.replace(
        needle,
        'db.collection("ratings").document(rid).set(m).addOnSuccessListener(q->{createAdminNotification("rating",rid,"تقييم جديد","يوجد تقييم جديد يحتاج مراجعة.");',
        1
    )

# 5) Complaint submission also creates the same admin review notification.
if 'db.collection("complaints").add(m).addOnSuccessListener' in s and 'createAdminNotification("complaint"' not in s:
    s=s.replace(
        'db.collection("complaints").add(m).addOnSuccessListener(x->{',
        'db.collection("complaints").add(m).addOnSuccessListener(x->{createAdminNotification("complaint","", "شكوى/اقتراح جديد","وصلت رسالة جديدة لخدمة العملاء وتحتاج متابعة.");',
        1
    )

# 6) Public contribution: add a single compact row without touching the existing visual design.
if "void installPublicContributionButtons()" not in s:
    methods=r'''    void installPublicContributionButtons(){
        if(homeStatus==null || homeStatus.getParent()==null)return;
        ViewGroup parent=(ViewGroup)homeStatus.getParent();
        if(parent.findViewWithTag("publicContributionRow")!=null)return;
        LinearLayout row=new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER);
        row.setTag("publicContributionRow");
        Button suggest=btn("🏪 ضيف محلك ووسع تجارتك وخلي الناس توصلك");
        Button service=btn("💬 الشكاوى والاقتراحات");
        for(Button b:new Button[]{suggest,service}){
            b.setAllCaps(false); b.setTextSize(12); b.setMinWidth(0); b.setMinHeight(0);
            b.setPadding(dp(4),0,dp(4),0);
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(52),1);
            lp.setMargins(dp(2),dp(2),dp(2),dp(2)); row.addView(b,lp);
        }
        suggest.setOnClickListener(v->showBusinessSuggestionDialog());
        service.setOnClickListener(v->show(servicePanel));
        int idx=parent.indexOfChild(homeStatus);
        parent.addView(row,Math.min(idx+1,parent.getChildCount()),new LinearLayout.LayoutParams(-1,dp(56)));
    }

    void showBusinessSuggestionDialog(){
        LinearLayout l=new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL); l.setPadding(dp(18),dp(8),dp(18),dp(6));
        EditText nm=new EditText(this); nm.setHint("اسم المنشأة / المحل *");
        Spinner cat=new Spinner(this);
        cat.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"مطاعم","محلات","عيادات","صيدليات","خدمات","أخرى"}));
        EditText ad=new EditText(this); ad.setHint("العنوان");
        EditText ph=new EditText(this); ph.setHint("رقم الهاتف (اختياري)"); ph.setInputType(3);
        EditText ds=new EditText(this); ds.setHint("وصف مختصر / الخدمات"); ds.setMinLines(3);
        l.addView(nm);l.addView(cat);l.addView(ad);l.addView(ph);l.addView(ds);
        new AlertDialog.Builder(this).setTitle("🏪 ضيف محلك ووسع تجارتك وخلي الناس توصلك")
            .setMessage("البيانات تُعرض على الإدارة للمراجعة أولًا ولن تظهر للعامة إلا بعد اعتماد الإدارة.")
            .setView(l).setPositiveButton("إرسال للإدارة",(d,w)->{
                FirebaseUser u=auth.getCurrentUser();
                if(u==null){toast("سجّل الدخول أولًا.");return;}
                String name=nm.getText().toString().trim();
                if(name.isEmpty()){toast("اكتب اسم المنشأة.");return;}
                Map<String,Object> m=new HashMap<>();
                m.put("name",name);m.put("category",cat.getSelectedItem().toString());
                m.put("address",ad.getText().toString().trim());m.put("phone",ph.getText().toString().trim());
                m.put("description",ds.getText().toString().trim());m.put("uid",u.getUid());
                m.put("status","pending");m.put("createdAt",FieldValue.serverTimestamp());
                db.collection("businessRequests").add(m).addOnSuccessListener(x->{
                    createAdminNotification("business",x.getId(),"اقتراح منشأة جديد","اقتراح منشأة جديد يحتاج مراجعة: "+name);
                    toast("✅ تم إرسال الاقتراح للإدارة.");
                }).addOnFailureListener(e->toast("تعذر إرسال الاقتراح: "+safe(e.getMessage())));
            }).setNegativeButton("إلغاء",null).show();
    }

'''
    marker="    void installBackHandler()"
    if marker not in s: raise SystemExit("MISSING: installBackHandler marker")
    s=s.replace(marker,methods+marker,1)

if "installPublicContributionButtons();" not in s:
    need("void setup(){","void setup(){\n        installPublicContributionButtons();","setup marker")

# V30's helper was removed by its method rewrite; restore only the Firestore notification writer.
if "void createAdminNotification(String type,String businessId,String title,String body)" not in s:
    pos=s.rfind("\n}")
    if pos<0: raise SystemExit("MISSING: class closing brace")
    helper_java=r'''    void createAdminNotification(String type,String businessId,String title,String body){
        if(db==null)return;
        Map<String,Object> n=new HashMap<>();
        n.put("type",type); n.put("businessId",businessId==null?"":businessId);
        n.put("title",title==null?"":title); n.put("body",body==null?"":body);
        n.put("status","pending"); n.put("createdAt",FieldValue.serverTimestamp());
        n.put("uid",auth!=null&&auth.getCurrentUser()!=null?auth.getCurrentUser().getUid():"");
        db.collection("adminNotifications").add(n);
    }
'''
    s=s[:pos]+"\n"+helper_java+s[pos:]


# ===== V33 stability/performance/image/owner fixes =====
# Imports needed for compressed Firestore image fallback.
if "import android.graphics.Bitmap;" not in s:
    s=s.replace("import android.graphics.Color;","import android.graphics.Color;\nimport android.graphics.Bitmap;\nimport android.graphics.BitmapFactory;")
if "import java.io.ByteArrayOutputStream;" not in s:
    s=s.replace("import java.io.File;","import java.io.File;\nimport java.io.ByteArrayOutputStream;\nimport java.io.InputStream;\nimport java.util.concurrent.Executors;")

# Smaller mobile pages prevent UI stalls and excessive Firestore reads.
s=s.replace('.whereEqualTo("status","approved").whereEqualTo("active",true).limit(200).get()',
            '.whereEqualTo("status","approved").whereEqualTo("active",true).limit(60).get()')
s=s.replace('.whereEqualTo("status","approved").whereEqualTo("active",true).whereEqualTo("featured",true).limit(100).get()',
            '.whereEqualTo("status","approved").whereEqualTo("active",true).whereEqualTo("featured",true).limit(40).get()')
s=s.replace('db.collection("businesses").limit(300).get()','db.collection("businesses").limit(150).get()')
s=s.replace('db.collection("offers").limit(300).get()','db.collection("offers").limit(150).get()')
s=s.replace('db.collection("complaints").limit(300).get()','db.collection("complaints").limit(150).get()')
s=s.replace('db.collection("ratings").limit(300).get()','db.collection("ratings").limit(150).get()')
s=s.replace('Glide.with(this).load(String.valueOf(o)).centerCrop().into(iv);',
            'Glide.with(this).load(String.valueOf(o)).override(dp(340),dp(260)).centerCrop().into(iv);')

# Store business name with every new rating, and avoid repeated name reads in admin.
s=s.replace(
'String rid=u.getUid()+"_"+bid; Map<String,Object>m=new HashMap<>(); m.put("businessId",bid); m.put("stars",selected[0]);',
'String rid=u.getUid()+"_"+bid; Map<String,Object>m=new HashMap<>(); m.put("businessId",bid); m.put("businessName",""); m.put("stars",selected[0]);',1)
s=s.replace(
'db.collection("ratings").document(rid).set(m).addOnSuccessListener(q->{createAdminNotification("rating",rid,"تقييم جديد","يوجد تقييم جديد يحتاج مراجعة.");toast("✅ تم إرسال تقييمك للمراجعة");dialog.dismiss();}).addOnFailureListener(e->hint.setText("تعذر إرسال التقييم. جرّب مرة أخرى."));',
'db.collection("businesses").document(bid).get().addOnSuccessListener(bd->{m.put("businessName",safe(bd.getString("name")));db.collection("ratings").document(rid).set(m).addOnSuccessListener(q->{createAdminNotification("rating",rid,"تقييم جديد","يوجد تقييم جديد يحتاج مراجعة.");toast("✅ تم إرسال تقييمك للمراجعة");dialog.dismiss();}).addOnFailureListener(e->hint.setText("تعذر إرسال التقييم. جرّب مرة أخرى."));}).addOnFailureListener(e->hint.setText("تعذر قراءة اسم المنشأة. جرّب مرة أخرى."));',1)
s=s.replace(
'if(!bid.isEmpty())db.collection("businesses").document(bid).get().addOnSuccessListener(bs->{String real=safe(bs.getString("name"));if(!real.isEmpty())h.setText("🏪 "+real);});',
'if(saved.isEmpty()&&!bid.isEmpty())db.collection("businesses").document(bid).get().addOnSuccessListener(bs->{String real=safe(bs.getString("name"));if(!real.isEmpty())h.setText("🏪 "+real);});',1)

# Complaints count on admin button.
s=s.replace(
'String[][] q={{"changeRequests","status","pending","طلبات",String.valueOf(R.id.btnAdminRequests)},{"offers","status","pending","عروض",String.valueOf(R.id.btnAdminOffers)},{"ratings","status","pending","تقييمات",String.valueOf(R.id.btnAdminRatings)}};',
'String[][] q={{"changeRequests","status","pending","طلبات",String.valueOf(R.id.btnAdminRequests)},{"offers","status","pending","عروض",String.valueOf(R.id.btnAdminOffers)},{"ratings","status","pending","تقييمات",String.valueOf(R.id.btnAdminRatings)},{"complaints","status","open","شكاوى",String.valueOf(R.id.btnAdminComplaints)}};',1)

# Owner edits can carry compressed photos through the approval request.
ownerOld='Map<String,Object>changes=businessFields(false);Map<String,Object>req=new HashMap<>();req.put("businessId",bid);req.put("ownerUid",u.getUid());req.put("changes",changes);req.put("status","pending");req.put("createdAt",FieldValue.serverTimestamp());addStatus.setText("☁️ جاري إرسال التعديل للمراجعة...");db.collection("changeRequests").add(req).addOnSuccessListener(x->addStatus.setText("✅ تم إرسال التعديل للإدارة. لن يظهر للعامة إلا بعد الموافقة.")).addOnFailureListener(e->addStatus.setText("❌ تعذر إرسال الطلب: "+safe(e.getMessage())));';
ownerNew='Map<String,Object>changes=businessFields(false); addStatus.setText(imageUris.isEmpty()?"☁️ جاري إرسال التعديل للمراجعة...":"🖼️ جاري تجهيز الصور ثم إرسال التعديل للمراجعة..."); encodeImagesForFirestoreAsync().addOnSuccessListener(imgs->{if(!imgs.isEmpty())changes.put("imageDataUrls",imgs);Map<String,Object>req=new HashMap<>();req.put("businessId",bid);req.put("ownerUid",u.getUid());req.put("changes",changes);req.put("status","pending");req.put("createdAt",FieldValue.serverTimestamp());db.collection("changeRequests").add(req).addOnSuccessListener(x->{imageUris.clear();renderThumbs();addStatus.setText("✅ تم إرسال التعديل للإدارة. لن يظهر للعامة إلا بعد الموافقة.");}).addOnFailureListener(e->addStatus.setText("❌ تعذر إرسال الطلب: "+safe(e.getMessage())));}).addOnFailureListener(e->addStatus.setText("❌ تعذر تجهيز الصور: "+safe(e.getMessage())));';
s=s.replace(ownerOld,ownerNew,1);

# If Firebase Storage is unavailable, keep small compressed copies in Firestore so photos still persist.
storageOld='saveBtn.setEnabled(true);saveBtn.setText("💾 حفظ البيانات");\n                    addStatus.setText("✅ تم حفظ بيانات المنشأة، لكن رفع الصور تعذر. يمكنك الضغط على حفظ مرة أخرى لإعادة المحاولة.\\n"+storageErrorMessage(e));';
storageNew='addStatus.setText("⚠️ التخزين السحابي للصور غير متاح، جاري حفظ نسخة صور مضغوطة داخل Firestore..."); encodeImagesForFirestoreAsync().addOnSuccessListener(imgs->{HashMap<String,Object> p=new HashMap<>();p.put("imageDataUrls",imgs);db.collection("businesses").document(id).set(p,SetOptions.merge()).addOnSuccessListener(z->{imageUris.clear();renderThumbs();finishBusinessSave(saveBtn,"✅ تم حفظ المنشأة والصور المضغوطة على السحابة.\\n⚠️ يفضل تفعيل Firebase Storage لاحقًا للصور الأصلية.");}).addOnFailureListener(x->{saveBtn.setEnabled(true);saveBtn.setText("💾 حفظ البيانات");addStatus.setText("❌ تعذر حفظ الصور: "+safe(x.getMessage()));});}).addOnFailureListener(x->{saveBtn.setEnabled(true);saveBtn.setText("💾 حفظ البيانات");addStatus.setText("❌ تعذر تجهيز الصور: "+safe(x.getMessage())+"\\n"+storageErrorMessage(e));});';
s=s.replace(storageOld,storageNew,1);

# Read Firestore imageDataUrls when Storage URLs are absent.
s=s.replace('Object imgsObj=d.get("imageUrls");\n        if(imgsObj instanceof List){',
            'Object imgsObj=d.get("imageUrls"); if(!(imgsObj instanceof List)||((List<?>)imgsObj).isEmpty())imgsObj=d.get("imageDataUrls");\n        if(imgsObj instanceof List){',1)

# Async compression: max 4 images, downsampled and JPEG-compressed.
marker='    void runOcr(Uri u)'
helpers='''    Task<List<String>> encodeImagesForFirestoreAsync(){
        ArrayList<Uri> copy=new ArrayList<>(imageUris);
        if(copy.isEmpty())return Tasks.forResult(new ArrayList<>());
        return Tasks.call(Executors.newSingleThreadExecutor(),()->{
            ArrayList<String> out=new ArrayList<>();
            int max=Math.min(copy.size(),4);
            for(int i=0;i<max;i++){String data=encodeImageDataUrl(copy.get(i));if(data!=null&&!data.isEmpty())out.add(data);}
            return out;
        });
    }
    String encodeImageDataUrl(Uri uri)throws Exception{
        if(uri==null)return "";
        android.content.ContentResolver cr=getContentResolver();
        BitmapFactory.Options bounds=new BitmapFactory.Options();bounds.inJustDecodeBounds=true;
        InputStream a=cr.openInputStream(uri);if(a==null)return "";BitmapFactory.decodeStream(a,null,bounds);a.close();
        int maxSide=Math.max(bounds.outWidth,bounds.outHeight),sample=1;while(maxSide/(sample*2)>1280)sample*=2;
        BitmapFactory.Options opts=new BitmapFactory.Options();opts.inSampleSize=Math.max(1,sample);opts.inPreferredConfig=Bitmap.Config.RGB_565;
        InputStream b=cr.openInputStream(uri);if(b==null)return "";Bitmap bmp=BitmapFactory.decodeStream(b,null,opts);b.close();if(bmp==null)return "";
        ByteArrayOutputStream out=new ByteArrayOutputStream();bmp.compress(Bitmap.CompressFormat.JPEG,58,out);bmp.recycle();
        return "data:image/jpeg;base64,"+Base64.getEncoder().encodeToString(out.toByteArray());
    
''';
s=s.replace(marker,helpers+marker,1);

p.write_text(s,encoding="utf-8")
print("V33 PERFORMANCE/IMAGES/OWNERS PATCH OK")
