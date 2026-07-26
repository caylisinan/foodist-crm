# Veritabanı Şeması (SQLite)

## Tablo İlişkileri (özet)

```
events (1) ──< buyers (N)
events (1) ──< participants (N)
buyers (1) ──< matches >── (1) participants
matches (1) ──< meetings (0..1)   [bir eşleşme en fazla bir toplantıya bağlanır]
meetings (1) ──< email_log (N)
matches (1) ──< email_log (N)
events (1) ──< import_mappings (N)
```

## events
Fuar edisyonu (ör. "Foodist İstanbul 2026").

| Alan | Tip | Açıklama |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | "Foodist İstanbul 2026" |
| start_date | DATE | |
| end_date | DATE | |
| venue | TEXT | "Tüyap Fuar ve Kongre Merkezi" |
| created_at | DATETIME | |

## users
| Alan | Tip | Açıklama |
|---|---|---|
| id | INTEGER PK | |
| username | TEXT UNIQUE | |
| password_hash | TEXT | SHA-256 (MVP; üretimde bcrypt önerilir) |
| full_name | TEXT | |
| role | TEXT | `admin` \| `operation` |
| created_at | DATETIME | |

## buyers  (Hosted Buyer)
| Alan | Tip | Açıklama |
|---|---|---|
| id | INTEGER PK | |
| event_id | INTEGER FK→events | |
| company_name | TEXT | |
| contact_name | TEXT | Yetkili ad soyad |
| country | TEXT | |
| contact_email | TEXT | |
| contact_phone | TEXT | |
| sector | TEXT | |
| interested_products | TEXT | virgülle ayrılmış |
| max_meetings | INTEGER | varsayılan 4 |
| max_minutes | INTEGER | varsayılan 60 |
| notes | TEXT | |
| created_at | DATETIME | |

## participants  (Katılımcı Firma)
| Alan | Tip | Açıklama |
|---|---|---|
| id | INTEGER PK | |
| event_id | INTEGER FK→events | |
| company_name | TEXT | |
| contact_name | TEXT | |
| country | TEXT | |
| contact_email | TEXT | |
| contact_phone | TEXT | |
| sector | TEXT | |
| offered_products | TEXT | virgülle ayrılmış |
| stand_no | TEXT | |
| notes | TEXT | |
| created_at | DATETIME | |

## matches
| Alan | Tip | Açıklama |
|---|---|---|
| id | INTEGER PK | |
| event_id | INTEGER FK→events | |
| buyer_id | INTEGER FK→buyers | |
| participant_id | INTEGER FK→participants | |
| product_score | FLOAT | 0–100 |
| sector_score | FLOAT | 0–100 |
| country_score | FLOAT | 0–100 |
| total_score | FLOAT | 0–100 ağırlıklı |
| status | TEXT | Önerildi / Onay Bekliyor / Buyer Onayladı / Katılımcı Onayladı / Karşılıklı Onaylandı / Toplantı Planlandı / Tamamlandı / No Show / Reddedildi |
| buyer_token | TEXT | onay linki token'ı |
| participant_token | TEXT | onay linki token'ı |
| buyer_responded_at | DATETIME NULL | |
| participant_responded_at | DATETIME NULL | |
| created_at | DATETIME | |

## meetings
| Alan | Tip | Açıklama |
|---|---|---|
| id | INTEGER PK | |
| match_id | INTEGER FK→matches UNIQUE | |
| event_id | INTEGER FK→events | |
| meeting_date | DATE | |
| start_time | TEXT | "10:00" |
| end_time | TEXT | "10:15" |
| stand_no | TEXT | |
| status | TEXT | Planlandı / Tamamlandı / Katılmadı |
| reminder_24h_sent | BOOLEAN | |
| reminder_1h_sent | BOOLEAN | |
| created_at | DATETIME | |

## email_log
| Alan | Tip | Açıklama |
|---|---|---|
| id | INTEGER PK | |
| match_id | INTEGER FK→matches NULL | |
| meeting_id | INTEGER FK→meetings NULL | |
| recipient_type | TEXT | buyer / participant |
| recipient_email | TEXT | |
| subject | TEXT | |
| status | TEXT | sent / failed |
| error | TEXT NULL | |
| sent_at | DATETIME | |

## import_mappings
Excel sütun eşleştirme şablonlarını hatırlar (her seferinde yeniden
eşleştirme yapmamak için).

| Alan | Tip | Açıklama |
|---|---|---|
| id | INTEGER PK | |
| entity_type | TEXT | buyer / participant |
| mapping_json | TEXT | `{"company_name":"Buyer Name","country":"Country",...}` |
| created_at | DATETIME | |

## app_settings
Anahtar-değer ayar deposu (SMTP bilgileri, skor ağırlıkları, eşleşme eşiği).

| Alan | Tip | Açıklama |
|---|---|---|
| key | TEXT PK | ör. `smtp_host`, `weight_product`, `match_threshold` |
| value | TEXT | |
