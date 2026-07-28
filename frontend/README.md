# amu-pulse — frontend

رابط کاربری «نبض طلا»: قیمت‌ها، تاریخچه، اخبار و خوانش جهت بازار.

Vue 3 (`<script setup>`) + TypeScript + Vite. تمام رابط فارسی و RTL است.

## راه‌اندازی

```bash
npm install
cp .env.example .env      # اختیاری؛ .env.development به‌صورت پیش‌فرض استفاده می‌شود
npm run dev               # http://localhost:5173
```

بک‌اند باید روی `VITE_PROXY_TARGET` (پیش‌فرض `http://127.0.0.1:8000`) بالا باشد.
درخواست‌های `/api` توسط پراکسی Vite به آن منتقل می‌شوند تا مرورگر در حالت توسعه
same-origin بماند.

Node ‏۲۰٫۱۹ یا بالاتر لازم است (`.nvmrc` روی ۲۲ تنظیم شده).

## دستورها

| دستور | کار |
| --- | --- |
| `npm run dev` | سرور توسعه |
| `npm run build` | type-check + بیلد پروداکشن در `dist/` |
| `npm run preview` | سرو کردن خروجی بیلد |
| `npm run type-check` | فقط بررسی تایپ‌ها |
| `npm test` | اجرای تست‌ها (Vitest) |
| `npm run test:watch` | تست در حالت watch |
| `npm run lint` | ESLint با `--fix` |
| `npm run format` | Prettier |

## ساختار

ساختار عمداً همان لایه‌بندی ماژولار بک‌اند را دنبال می‌کند:

```
src/
├── core/           # هسته‌ی اپ: پیکربندی، روتر، pinia، بوت‌استرپ ماژول‌ها
│   ├── config/     # env.ts، locale.ts
│   ├── router/
│   ├── module.ts   # قرارداد AppModule + defineModule()
│   └── bootstrap.ts
├── infra/          # لایه‌ی زیرساخت — بیرون از دامنه‌ی کسب‌وکار
│   └── http/       # کلاینت axios، باز کردن envelope، ApiRequestError، توکن
├── common/         # چیزهای مشترک بین ماژول‌ها
│   ├── types/      # قرارداد پاسخ API
│   ├── utils/      # فرمت اعداد و تاریخ فارسی
│   ├── composables/
│   ├── components/ # BaseCard، BaseSpinner، ErrorState، EmptyState
│   └── layout/     # AppShell، AppHeader، AppFooter
└── modules/        # ماژول‌های ویژگی‌محور، هرکدام خودکفا
    ├── dashboard/
    ├── prices/     # components · services · stores · types · views
    ├── analysis/
    ├── news/
    └── system/     # صفحه‌های فرا-ویژگی (۴۰۴ و بعدها health)
```

### افزودن یک ماژول

پوشه‌ی `src/modules/<name>/` را بسازید و در `index.ts` آن یک ماژول export کنید:

```ts
import { defineModule } from '@/core/module'

export default defineModule({
  name: 'aggregations',
  routes: [
    {
      path: '/aggregations',
      name: 'aggregations',
      component: () => import('./views/AggregationsView.vue'),
      meta: { title: 'تجمیع‌ها', nav: { label: 'تجمیع‌ها', order: 50 } },
    },
  ],
})
```

همین. `core/bootstrap.ts` با `import.meta.glob` ماژول‌ها را در زمان بیلد پیدا
می‌کند — درست مثل `boot_routers` در بک‌اند — پس نه روتر و نه منوی بالای صفحه
نیازی به ویرایش دستی ندارند. مسیرِ catch-all همیشه آخر ثبت می‌شود و منو بر اساس
`meta.nav.order` مرتب می‌شود.

هر ماژول مسیرهای API خودش را در `services/` نگه می‌دارد؛ فایل متمرکز آدرس‌ها وجود ندارد.

## لایه‌ی HTTP

بک‌اند همه‌چیز را در یک envelope برمی‌گرداند:

```jsonc
{ "success": true, "data": …, "meta": …, "error": null, "errors": null }
```

`infra/http` این پوشش را باز می‌کند: سرویس‌ها مستقیم `data` می‌گیرند و هر خطا —
شبکه، تایم‌اوت، خطای HTTP یا `success: false` — به‌شکل یک `ApiRequestError`
بالا می‌آید. پس هیچ‌کجای اپ لازم نیست جزئیات axios را بشناسد.

```ts
const quotes = await pricesService.latest(['GOLD_18K']) // PriceQuote[]
```

توکن JWT در `localStorage` نگه‌داری می‌شود و روی هر درخواست ست می‌شود؛ پاسخ ۴۰۱
توکن را پاک می‌کند و کاربر را به صفحه‌ی اصلی برمی‌گرداند.

## فارسی‌سازی

- `index.html` با `lang="fa"` و `dir="rtl"`؛ `main.ts` هم آن را تثبیت می‌کند.
- فونت **Vazirmatn Variable** به‌صورت self-host (بدون CDN) از
  `@fontsource-variable/vazirmatn`.
- همه‌ی فرمت‌ها از `fa-IR` استفاده می‌کنند، پس ارقام فارسی و تقویم جلالی
  به‌صورت پیش‌فرض درست درمی‌آیند — `common/utils/format.ts`.
- قیمت‌ها به تومان با `formatToman()`؛ انس جهانی و دلار با `formatUsd()`.
- Tailwind v4 با توکن‌های `--color-sell` / `--color-hold` / `--color-buy` برای
  طیف قرمزِ فروش تا سبزِ خرید.
- گیج تحلیل عمداً LTR می‌ماند (محور فروش→خرید) و با برچسب فارسی مشخص شده است.

## نکته‌ها

- امتیاز تحلیل در بازه‌ی `[-1, 1]` است و همیشه با `confidence` و `reason`
  همراه می‌آید؛ هر سه در رابط نمایش داده می‌شوند.
- خروجی «خوانش بازار» است، نه توصیه‌ی مالی — این جمله در فوتر ثابت است.
- `npm audit` چند مورد high روی زنجیره‌ی `@vue/test-utils → js-beautify` گزارش
  می‌کند. فقط dev-dependency است و در باندل نهایی نمی‌آید؛ رفعشان نیاز به
  breaking change دارد.
