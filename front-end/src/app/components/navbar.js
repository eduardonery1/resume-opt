import Image from "next/image";
import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="h-16 w-full flex justify-between items-center bg-[var(--navbar)] p-2">
      <div>
        <Image src="/logo.png" alt="the logo is a drawn bird" width={50} height={50} />
      </div>
      <div className="flex gap-4">
        <Link href="/" className="text-[var(--background)] text-lg hover:text-[var(--navlinks-holder)] focus:underline">Home</Link>
        <Link href="/optimizer" className="text-[var(--background)] text-lg hover:text-[var(--navlinks-holder)] focus:underline">Optimizer</Link>
        <Link href="/about" className="text-[var(--background)] text-lg hover:text-[var(--navlinks-holder)] focus:underline">About Us</Link>
        <Link href="/contact" className="text-[var(--background)] text-lg hover:text-[var(--navlinks-holder)] focus:underline">Contact</Link>
      </div>
      <button className="flex justify-center items-center bg-transparent h-[50%] border-none"><Image src="/menu-icon.svg" alt="three bars lying down" width={35} height={35} /></button>
    </nav>
  )
}