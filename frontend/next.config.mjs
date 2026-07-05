/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: { workerThreads: false, cpus: 1 },
};
export default nextConfig;
