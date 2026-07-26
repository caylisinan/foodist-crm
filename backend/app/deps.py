"""
Basit rol kontrolü. Frontend her istekte X-User-Role header'ı gönderir
(giriş sırasında dönen role bilgisine göre). Bu, admin-only işlemlerin
sadece arayüzde gizlenmesi değil, API seviyesinde de korunmasını sağlar
— paylaşımlı/web senaryosunda önemlidir çünkü artık birden fazla kişi
aynı backend'e erişebiliyor.

Not: Bu MVP seviyesinde bir kontroldür (token/oturum imzalama yok);
header istemci tarafından gönderildiği için sunucu tarafında
doğrulanmıyor. Gerçek üretim ortamı için imzalı oturum/JWT önerilir.
"""
from fastapi import Header, HTTPException


def require_admin(x_user_role: str = Header(default="operation")):
    if x_user_role != "admin":
        raise HTTPException(403, "Bu işlem için admin yetkisi gereklidir.")
    return x_user_role
