import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ArrowRight, Upload, Zap, Database, CheckCircle } from "lucide-react";
import heroImage from "@/assets/hero-transformation.jpg";

const Home = () => {
  return (
    <div className="overflow-hidden">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center bg-gradient-mesh">
        <div className="absolute inset-0 bg-gradient-to-br from-background/95 to-background/70" />
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Content */}
            <div className="space-y-8 animate-fade-in">
              <div className="space-y-4">
                <h1 className="text-5xl lg:text-6xl font-bold leading-tight">
                  From P&ID to{" "}
                  <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                    Digital Intelligence
                  </span>
                </h1>
                <p className="text-xl text-muted-foreground max-w-2xl">
                  Transform traditional Process & Instrumentation Diagrams into intelligent, 
                  structured datasets with our AI-powered recognition and validation system.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  asChild
                  variant="gradient"
                  size="xl"
                >
                  <Link to="/upload">
                    <Upload className="mr-2 h-5 w-5" />
                    Upload P&ID
                  </Link>
                </Button>
                
                <Button
                  variant="outline-glow"
                  size="xl"
                  asChild
                >
                  <Link to="/about">
                    Explore Demo
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Link>
                </Button>
              </div>

              {/* Stats */}
              <div className="flex gap-8 pt-8">
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary">99.2%</div>
                  <div className="text-sm text-muted-foreground">Accuracy</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-secondary">10x</div>
                  <div className="text-sm text-muted-foreground">Faster</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary">500+</div>
                  <div className="text-sm text-muted-foreground">Projects</div>
                </div>
              </div>
            </div>

            {/* Right Image */}
            <div className="relative animate-slide-in">
              <div className="relative rounded-2xl overflow-hidden shadow-elegant">
                <img
                  src={heroImage}
                  alt="P&ID to Digital Transformation"
                  className="w-full h-auto object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-secondary/20" />
              </div>
              
              {/* Floating Elements */}
              <div className="absolute -top-4 -right-4 bg-card border border-border rounded-xl p-4 shadow-industrial animate-float">
                <Zap className="h-8 w-8 text-secondary" />
              </div>
              <div className="absolute -bottom-4 -left-4 bg-card border border-border rounded-xl p-4 shadow-industrial animate-float" style={{ animationDelay: '1s' }}>
                <Database className="h-8 w-8 text-primary" />
              </div>
            </div>
          </div>
        </div>

        {/* Animated Background Elements */}
        <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-primary via-secondary to-primary animate-pipeline-flow opacity-50" />
      </section>

      {/* Features Section */}
      <section className="py-20 bg-card/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Unlock Smart Engineering</h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Our AI-powered platform transforms static P&ID diagrams into dynamic, 
              queryable digital assets that integrate seamlessly with your workflow.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: <Upload className="h-8 w-8" />,
                title: "Smart Upload",
                description: "Support for PDF, images, and CAD files with intelligent format detection"
              },
              {
                icon: <Zap className="h-8 w-8" />,
                title: "AI Recognition",
                description: "Advanced computer vision extracts equipment, connections, and metadata"
              },
              {
                icon: <CheckCircle className="h-8 w-8" />,
                title: "Human Validation",
                description: "Interactive review process ensures 100% accuracy before export"
              }
            ].map((feature, index) => (
              <Card key={index} className="p-8 hover:shadow-elegant transition-all duration-300 group cursor-pointer">
                <div className="text-primary mb-4 group-hover:text-secondary transition-colors duration-300">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-primary">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-primary-foreground mb-4">
            Ready to Digitize Your P&IDs?
          </h2>
          <p className="text-xl text-primary-foreground/80 mb-8">
            Join hundreds of engineering teams already using PIDFlow to accelerate their digital transformation.
          </p>
                <Button
                  asChild
                  variant="gradient-secondary"
                  size="xl"
                >
                  <Link to="/upload">
                    Get Started Now
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Link>
                </Button>
        </div>
      </section>
    </div>
  );
};

export default Home;