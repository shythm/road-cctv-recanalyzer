import { Outlet, Link } from "react-router-dom";

function RootPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <header className="container mb-4">
        <h1 className="py-8 font-bold text-3xl">
          <Link to="/">고속도로 CCTV 영상 분석 시스템</Link>
        </h1>
        <nav className="space-x-6 text-lg">
          <Link to="/record">CCTV 녹화하기</Link>
          <Link to="/track">CCTV 영상 차량 추적하기</Link>
          <Link to="/analyze">차량 추적 데이터 분석하기</Link>
        </nav>
      </header>
      <main className="container">
        <Outlet />
      </main>
      {/* footer */}
      <footer className="mb-8"></footer>
    </div>
  );
}

export default RootPage;
