import { Outlet } from "react-router-dom";

function RootPage() {
  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* header */}
      <header>
        <h1>고속도로 CCTV 영상 분석 시스템</h1>
      </header>
      {/* main */}
      <main>
        {/* left side */}
        <aside className="w-64 h-screen">
          <nav className="h-full p-3 overflow-y-auto bg-gray-100">
            <ul>
              <li>
                <a href="/cctv">CCTV 목록</a>
              </li>
              <li>
                <a href="/record">CCTV 영상 녹화</a>
              </li>
              <li>
                <a href="/tracking">CCTV 영상 차량 추적</a>
              </li>
              <li>
                <a href="/report">차량 추적 데이터 분석</a>
              </li>
            </ul>
          </nav>
        </aside>
        {/* right side */}
        <section>
          <Outlet />
        </section>
      </main>
      {/* footer */}
      <footer></footer>
    </div>
  );
}

export default RootPage;
