import type { Metadata } from "next";
import "./globals.css";
import Nav from "@/components/Nav";
import ClientErrorBoundary from "@/components/ClientErrorBoundary";

export const metadata: Metadata = {
  title: "Agent Memory Testbench",
  description:
    "Compare memory architectures, trace where answers fail, and rerun versioned evidence from one open testbench.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen" style={{ background: "var(--background)", color: "var(--foreground)" }}>
        <Nav />
        <main>
          <ClientErrorBoundary>{children}</ClientErrorBoundary>
        </main>
        <footer className="border-t mt-16 py-8 text-center text-sm" style={{ borderColor: "var(--border)", color: "var(--muted)" }}>
          <a
            href="https://github.com/xmpuspus/agent-memory-testbench"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:opacity-70 transition-opacity"
            style={{ color: "var(--accent)" }}
          >
            GitHub
          </a>
          <span className="mx-2">·</span>
          <span>Agent Memory Testbench</span>
        </footer>
      </body>
    </html>
  );
}
