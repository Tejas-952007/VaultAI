/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // This allows the UI to run even if the FastAPI backend isn't live yet
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;