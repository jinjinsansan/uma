/** @type {import('next').NextConfig} */
const nextConfig = {
  // output: 'export', // NextAuth.jsはサーバーサイドAPIが必要なためコメントアウト
  trailingSlash: true,
  images: {
    unoptimized: true
  },
};

module.exports = nextConfig;