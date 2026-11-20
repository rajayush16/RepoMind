import { Navbar } from "@/components/marketing/navbar";
import { Hero } from "@/components/marketing/hero";
import { Features } from "@/components/marketing/features";
import { HowItWorks } from "@/components/marketing/how-it-works";
import { ArchitectureShowcase } from "@/components/marketing/architecture-showcase";
import { Languages } from "@/components/marketing/languages";
import { UseCases } from "@/components/marketing/use-cases";
import { Security } from "@/components/marketing/security";
import { Cta } from "@/components/marketing/cta";
import { Footer } from "@/components/marketing/footer";

export default function LandingPage() {
  return (
    <div className="flex min-h-dvh flex-col bg-background text-foreground">
      <Navbar />
      <main className="flex-1">
        <Hero />
        <Features />
        <HowItWorks />
        <ArchitectureShowcase />
        <Languages />
        <UseCases />
        <Security />
        <Cta />
      </main>
      <Footer />
    </div>
  );
}
