import { motion } from 'framer-motion';

export default function GradientBackground() {
  return (
    <motion.div
      className="fixed inset-0 -z-10"
      style={{
        background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #1e3c72 100%)',
      }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1 }}
    >
      <div className="absolute inset-0 bg-black/20" />
    </motion.div>
  );
}